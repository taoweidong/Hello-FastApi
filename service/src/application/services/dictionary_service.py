"""应用层 - 字典服务。

提供字典相关的业务逻辑，包括字典的增删改查等操作。
"""

from src.application.dto.dictionary_dto import DictionaryCreateDTO, DictionaryListQueryDTO, DictionaryResponseDTO, DictionaryUpdateDTO
from src.domain.entities.dictionary import DictionaryEntity
from src.domain.exceptions import BusinessError, NotFoundError
from src.domain.repositories.dictionary_repository import DictionaryRepositoryInterface


class DictionaryService:
    """字典领域操作的应用服务。"""

    def __init__(self, dict_repo: DictionaryRepositoryInterface):
        self.dict_repo = dict_repo

    async def get_dictionaries(self, query: DictionaryListQueryDTO) -> list[DictionaryResponseDTO]:
        """获取字典列表（扁平结构，前端自动转树）。"""
        all_dicts = await self.dict_repo.get_all()

        # 前端筛选
        filtered_dicts = all_dicts
        if query.name:
            filtered_dicts = [d for d in filtered_dicts if query.name in d.name]
        if query.isActive is not None:
            filtered_dicts = [d for d in filtered_dicts if d.is_active == query.isActive]

        return [self._to_response(d) for d in filtered_dicts]

    async def get_dictionary_by_name(self, name: str) -> list[DictionaryResponseDTO]:
        """根据字典名称查询字典项。"""
        all_dicts = await self.dict_repo.get_all()
        filtered_dicts = [d for d in all_dicts if name in d.name]
        return [self._to_response(d) for d in filtered_dicts]

    async def create_dictionary(self, dto: DictionaryCreateDTO) -> DictionaryResponseDTO:
        """创建字典。"""
        # 处理 parentId
        parent_id = dto.parentId
        if parent_id:
            parent = await self.dict_repo.get_by_id(parent_id)
            if not parent:
                raise BusinessError("父字典不存在")

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
        return self._to_response(created)

    async def update_dictionary(self, dict_id: str, dto: DictionaryUpdateDTO) -> DictionaryResponseDTO:
        """更新字典。"""
        dictionary = await self.dict_repo.get_by_id(dict_id)
        if not dictionary:
            raise NotFoundError("字典不存在")

        # 处理 parentId
        if dto.parentId is not None:
            if dictionary.is_circular_reference(dto.parentId):
                raise BusinessError("不能将字典设为自己的子字典")
            if dto.parentId:
                parent = await self.dict_repo.get_by_id(dto.parentId)
                if not parent:
                    raise BusinessError("父字典不存在")
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
        return self._to_response(updated)

    async def delete_dictionary(self, dict_id: str) -> bool:
        """删除字典。"""
        dictionary = await self.dict_repo.get_by_id(dict_id)
        if not dictionary:
            raise NotFoundError("字典不存在")

        # 检查是否有子字典
        children = await self.dict_repo.get_by_parent_id(dict_id)
        if children:
            raise BusinessError("字典下存在子字典，不能删除")

        return await self.dict_repo.delete(dict_id)

    @staticmethod
    def _to_response(dictionary: DictionaryEntity) -> DictionaryResponseDTO:
        """将字典实体转换为响应 DTO。"""
        return DictionaryResponseDTO(id=dictionary.id, parentId=dictionary.parent_id, name=dictionary.name, label=dictionary.label, value=dictionary.value, sort=dictionary.sort, isActive=dictionary.is_active, createdTime=dictionary.created_time, updatedTime=dictionary.updated_time, description=dictionary.description)
