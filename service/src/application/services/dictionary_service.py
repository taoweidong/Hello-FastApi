"""应用层 - 字典服务。

提供字典相关的业务逻辑，包括字典的增删改查、
面向业务表单的字典取数（带 Redis 缓存）等操作。
"""

from typing import Any

from src.application.dto.dictionary_dto import (
    DictionaryCreateDTO,
    DictionaryListQueryDTO,
    DictionaryResponseDTO,
    DictionaryUpdateDTO,
)
from src.domain.entities.dictionary import DictionaryEntity
from src.domain.error_messages import ErrorMessages as EM
from src.domain.exceptions import BusinessError, NotFoundError
from src.domain.repositories.dictionary_repository import DictionaryRepositoryInterface
from src.domain.services.cache_port import CachePort


class DictionaryService:
    """字典领域操作的应用服务。"""

    # 向上追溯根字典的最大层级，防止异常数据导致死循环
    _MAX_ROOT_TRACE_DEPTH = 32

    def __init__(self, dict_repo: DictionaryRepositoryInterface, cache_service: CachePort | None = None):
        self.dict_repo = dict_repo
        self.cache_service = cache_service

    async def get_dictionaries(self, query: DictionaryListQueryDTO) -> list[DictionaryResponseDTO]:
        """获取字典列表（数据库级别过滤，扁平结构，前端自动转树）。"""
        dictionaries = await self.dict_repo.get_filtered(name=query.name, is_active=query.isActive)
        return [self._to_response(d) for d in dictionaries]

    async def get_dictionary_by_name(self, name: str) -> list[DictionaryResponseDTO]:
        """根据字典名称查询字典项。"""
        dictionaries = await self.dict_repo.get_filtered(name=name)
        return [self._to_response(d) for d in dictionaries]

    async def get_dict_items_by_type(self, dict_name: str) -> list[dict[str, Any]]:
        """根据字典类型名称获取启用状态的字典项（供业务表单联动）。

        优先读取缓存（dict:{name}），未命中时查库并回填缓存。
        返回按 sort 升序的字典项列表，每项含 label/value。
        """
        # 缓存优先
        if self.cache_service is not None:
            cached = await self.cache_service.get_dict_items(dict_name)
            if cached is not None:
                return cached

        # 精确匹配字典类型（根节点），取其启用状态的子项
        items: list[dict[str, Any]] = []
        root = await self.dict_repo.get_by_name(dict_name)
        if root is not None:
            children = await self.dict_repo.get_by_parent_id(root.id)
            items = [
                {"label": child.label, "value": child.value}
                for child in sorted(children, key=lambda d: d.sort)
                if child.is_active
            ]

        # 回填缓存（含空列表，防止穿透）
        if self.cache_service is not None:
            await self.cache_service.set_dict_items(dict_name, items)
        return items

    async def create_dictionary(self, dto: DictionaryCreateDTO) -> DictionaryResponseDTO:
        """创建字典。"""
        # 处理 parentId
        parent_id = dto.parentId
        if parent_id:
            parent = await self.dict_repo.get_by_id(parent_id)
            if not parent:
                raise BusinessError(EM.PARENT_DICTIONARY_NOT_FOUND)

        # 处理排序：若未指定则自动计算同级最大值+1
        sort_value = dto.sort
        if sort_value is None:
            max_sort = await self.dict_repo.get_max_sort(parent_id)
            sort_value = max_sort + 1

        # 创建字典
        dictionary = DictionaryEntity.create_new(
            name=dto.name,
            label=dto.label,
            value=dto.value,
            sort=sort_value,
            parent_id=parent_id,
            description=dto.description,
        )
        dictionary.is_active = dto.isActive

        created = await self.dict_repo.create(dictionary)
        # 新增子项影响所属根字典的缓存数据，执行失效
        if created.parent_id:
            root_name = await self._resolve_root_name(created.name, created.parent_id)
            await self._invalidate_dict_cache({root_name})
        return self._to_response(created)

    async def update_dictionary(self, dict_id: str, dto: DictionaryUpdateDTO) -> DictionaryResponseDTO:
        """更新字典。"""
        dictionary = await self.dict_repo.get_by_id(dict_id)
        if not dictionary:
            raise NotFoundError(EM.DICTIONARY_NOT_FOUND)

        # 记录更新前快照，用于缓存失效（父节点/名称变更时需失效新旧两个根字典）
        old_name, old_parent_id = dictionary.name, dictionary.parent_id

        # 处理 parentId
        if dto.parentId is not None:
            if dictionary.is_circular_reference(dto.parentId):
                raise BusinessError(EM.DICTIONARY_CIRCULAR_REFERENCE)
            if dto.parentId:
                parent = await self.dict_repo.get_by_id(dto.parentId)
                if not parent:
                    raise BusinessError(EM.PARENT_DICTIONARY_NOT_FOUND)
            dictionary.parent_id = dto.parentId or None

        dictionary.update_info(
            name=dto.name,
            label=dto.label,
            value=dto.value,
            sort=dto.sort,
            is_active=dto.isActive,
            description=dto.description,
        )

        updated = await self.dict_repo.update(dictionary)
        # 缓存失效：旧根字典必失效；父节点或名称变更时同步失效新根字典
        invalidate_names = {await self._resolve_root_name(old_name, old_parent_id)}
        if updated.parent_id is None:
            invalidate_names.add(updated.name)
        else:
            invalidate_names.add(await self._resolve_root_name(updated.name, updated.parent_id))
        await self._invalidate_dict_cache(invalidate_names)
        return self._to_response(updated)

    async def delete_dictionary(self, dict_id: str) -> bool:
        """删除字典。"""
        dictionary = await self.dict_repo.get_by_id(dict_id)
        if not dictionary:
            raise NotFoundError(EM.DICTIONARY_NOT_FOUND)

        # 检查是否有子字典
        children = await self.dict_repo.get_by_parent_id(dict_id)
        if children:
            raise BusinessError(EM.DICTIONARY_HAS_CHILDREN)

        # 删除前先追溯所属根字典，删除成功后失效其缓存
        root_name = await self._resolve_root_name(dictionary.name, dictionary.parent_id)
        result = await self.dict_repo.delete(dict_id)
        if result:
            await self._invalidate_dict_cache({root_name})
        return result

    async def _resolve_root_name(self, node_name: str, parent_id: str | None) -> str:
        """沿 parent_id 向上追溯至根字典，返回根字典名称。

        若节点本身即根字典（无父节点），直接返回自身名称。
        """
        current_name = node_name
        current_parent = parent_id
        depth = 0
        while current_parent and depth < self._MAX_ROOT_TRACE_DEPTH:
            parent = await self.dict_repo.get_by_id(current_parent)
            if parent is None:
                break
            current_name = parent.name
            current_parent = parent.parent_id
            depth += 1
        return current_name

    async def _invalidate_dict_cache(self, dict_names: set[str]) -> None:
        """批量失效字典数据缓存（无缓存服务时静默跳过）。"""
        if self.cache_service is None:
            return
        for name in dict_names:
            await self.cache_service.invalidate_dict(name)

    @staticmethod
    def _to_response(dictionary: DictionaryEntity) -> DictionaryResponseDTO:
        """将字典实体转换为响应 DTO。"""
        return DictionaryResponseDTO(
            id=dictionary.id,
            parentId=dictionary.parent_id,
            name=dictionary.name,
            label=dictionary.label,
            value=dictionary.value,
            sort=dictionary.sort,
            isActive=dictionary.is_active,
            createdTime=dictionary.created_time,
            updatedTime=dictionary.updated_time,
            description=dictionary.description,
        )
