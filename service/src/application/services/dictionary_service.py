"""应用层 - 字典服务。

提供字典相关的业务逻辑，包括字典的增删改查等操作。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.dictionary_dto import DictionaryCreateDTO, DictionaryListQueryDTO, DictionaryResponseDTO, DictionaryUpdateDTO
from src.domain.exceptions import BusinessError, NotFoundError
from src.domain.repositories.dictionary_repository import DictionaryRepositoryInterface
from src.infrastructure.database.models import Dictionary


class DictionaryService:
    """字典领域操作的应用服务。"""

    def __init__(self, session: AsyncSession, dict_repo: DictionaryRepositoryInterface):
        """初始化字典服务。

        Args:
            session: 数据库会话，用于事务控制
            dict_repo: 字典仓储接口实例
        """
        self.session = session
        self.dict_repo = dict_repo

    async def get_dictionaries(self, query: DictionaryListQueryDTO) -> list[DictionaryResponseDTO]:
        """获取字典列表（扁平结构，前端自动转树）。

        Args:
            query: 查询参数

        Returns:
            字典列表
        """
        all_dicts = await self.dict_repo.get_all(session=self.session)

        # 前端筛选
        filtered_dicts = all_dicts
        if query.name:
            filtered_dicts = [d for d in filtered_dicts if query.name in d.name]
        if query.isActive is not None:
            filtered_dicts = [d for d in filtered_dicts if d.is_active == query.isActive]

        return [self._to_response(d) for d in filtered_dicts]

    async def get_dictionary_by_name(self, name: str) -> list[DictionaryResponseDTO]:
        """根据字典名称查询字典项。

        Args:
            name: 字典名称

        Returns:
            匹配的字典列表
        """
        all_dicts = await self.dict_repo.get_all(session=self.session)
        filtered_dicts = [d for d in all_dicts if name in d.name]
        return [self._to_response(d) for d in filtered_dicts]

    async def create_dictionary(self, dto: DictionaryCreateDTO) -> DictionaryResponseDTO:
        """创建字典。

        Args:
            dto: 创建请求

        Returns:
            创建的字典
        """
        # 处理 parentId
        parent_id = dto.parentId
        if parent_id:
            # 验证父字典是否存在
            parent = await self.dict_repo.get_by_id(parent_id, session=self.session)
            if not parent:
                raise BusinessError("父字典不存在")

        # 处理排序：若未指定则自动计算同级最大值+1
        sort_value = dto.sort
        if sort_value is None:
            max_sort = await self.dict_repo.get_max_sort(parent_id, session=self.session)
            sort_value = max_sort + 1

        # 创建字典
        dictionary = Dictionary(name=dto.name, label=dto.label, value=dto.value, parent_id=parent_id, sort=sort_value, is_active=dto.isActive, description=dto.description)

        await self.dict_repo.create(dictionary, session=self.session)
        await self.session.flush()
        # 重新获取以确保返回完整模型
        created = await self.dict_repo.get_by_id(dictionary.id, session=self.session)
        if created is None:
            raise BusinessError("字典创建后无法加载")
        return self._to_response(created)

    async def update_dictionary(self, dict_id: str, dto: DictionaryUpdateDTO) -> DictionaryResponseDTO:
        """更新字典。

        Args:
            dict_id: 字典ID
            dto: 更新请求

        Returns:
            更新后的字典

        Raises:
            NotFoundError: 字典不存在
            BusinessError: 不能将字典设为自己的子字典
        """
        dictionary = await self.dict_repo.get_by_id(dict_id, session=self.session)
        if not dictionary:
            raise NotFoundError("字典不存在")

        # 处理 parentId
        if dto.parentId is not None:
            if dto.parentId == dict_id:
                raise BusinessError("不能将字典设为自己的子字典")
            if dto.parentId:
                parent = await self.dict_repo.get_by_id(dto.parentId, session=self.session)
                if not parent:
                    raise BusinessError("父字典不存在")
            dictionary.parent_id = dto.parentId or None

        # 更新字段
        if dto.name is not None:
            dictionary.name = dto.name
        if dto.label is not None:
            dictionary.label = dto.label
        if dto.value is not None:
            dictionary.value = dto.value
        if dto.sort is not None:
            dictionary.sort = dto.sort
        if dto.isActive is not None:
            dictionary.is_active = dto.isActive
        if dto.description is not None:
            dictionary.description = dto.description

        await self.dict_repo.update(dictionary, session=self.session)
        await self.session.flush()
        # 重新获取以确保返回完整模型
        updated = await self.dict_repo.get_by_id(dict_id, session=self.session)
        if updated is None:
            raise NotFoundError("字典不存在")
        return self._to_response(updated)

    async def delete_dictionary(self, dict_id: str) -> bool:
        """删除字典。

        Args:
            dict_id: 字典ID

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 字典不存在
            BusinessError: 字典下存在子字典
        """
        dictionary = await self.dict_repo.get_by_id(dict_id, session=self.session)
        if not dictionary:
            raise NotFoundError("字典不存在")

        # 检查是否有子字典
        children = await self.dict_repo.get_by_parent_id(dict_id, session=self.session)
        if children:
            raise BusinessError("字典下存在子字典，不能删除")

        success = await self.dict_repo.delete(dict_id, session=self.session)
        await self.session.flush()
        return success

    @staticmethod
    def _to_response(dictionary: Dictionary) -> DictionaryResponseDTO:
        """将 Dictionary 模型转换为响应 DTO。"""
        return DictionaryResponseDTO(id=dictionary.id, parentId=dictionary.parent_id, name=dictionary.name, label=dictionary.label, value=dictionary.value, sort=dictionary.sort, isActive=dictionary.is_active, createdTime=dictionary.created_time, updatedTime=dictionary.updated_time, description=dictionary.description)
