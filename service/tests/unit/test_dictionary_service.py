"""字典服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.dictionary_dto import DictionaryCreateDTO, DictionaryListQueryDTO, DictionaryUpdateDTO
from src.application.services.dictionary_service import DictionaryService
from src.domain.entities.dictionary import DictionaryEntity
from src.domain.exceptions import BusinessError, NotFoundError


@pytest.mark.unit
class TestDictionaryService:
    """DictionaryService 测试类。"""

    @pytest.fixture
    def mock_dict_repo(self):
        """创建模拟字典仓储。"""
        repo = AsyncMock()
        repo.get_all = AsyncMock(return_value=[])
        repo.get_filtered = AsyncMock(return_value=[])
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_by_parent_id = AsyncMock(return_value=[])
        repo.get_max_sort = AsyncMock(return_value=0)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def dict_service(self, mock_dict_repo):
        """创建字典服务实例。"""
        return DictionaryService(dict_repo=mock_dict_repo)

    @pytest.mark.asyncio
    async def test_get_dictionaries_empty(self, dict_service, mock_dict_repo):
        """测试获取空字典列表。"""
        mock_dict_repo.get_filtered = AsyncMock(return_value=[])
        query = DictionaryListQueryDTO()
        result = await dict_service.get_dictionaries(query)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_dictionaries_with_name_filter(self, dict_service, mock_dict_repo):
        """测试按名称筛选字典。"""
        d1 = DictionaryEntity(id="1", name="status", label="状态")
        mock_dict_repo.get_filtered = AsyncMock(return_value=[d1])
        query = DictionaryListQueryDTO(name="status")
        result = await dict_service.get_dictionaries(query)
        assert len(result) == 1
        assert result[0].name == "status"

    @pytest.mark.asyncio
    async def test_get_dictionary_by_name(self, dict_service, mock_dict_repo):
        """测试按名称查询字典。"""
        d1 = DictionaryEntity(id="1", name="status_type")
        d2 = DictionaryEntity(id="2", name="status")
        mock_dict_repo.get_filtered = AsyncMock(return_value=[d1, d2])
        result = await dict_service.get_dictionary_by_name("status")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_create_dictionary_success(self, dict_service, mock_dict_repo):
        """测试创建字典成功。"""
        created = DictionaryEntity(id="1", name="status", label="状态", value="1", sort=1)
        mock_dict_repo.create = AsyncMock(return_value=created)

        dto = DictionaryCreateDTO(name="status", label="状态", value="1", isActive=1)
        result = await dict_service.create_dictionary(dto)
        assert result.name == "status"

    @pytest.mark.asyncio
    async def test_create_dictionary_with_parent(self, dict_service, mock_dict_repo):
        """测试创建带父级的字典成功。"""
        parent = DictionaryEntity(id="p1", name="parent")
        mock_dict_repo.get_by_id = AsyncMock(return_value=parent)
        created = DictionaryEntity(id="1", name="child", parent_id="p1")
        mock_dict_repo.create = AsyncMock(return_value=created)

        dto = DictionaryCreateDTO(name="child", parentId="p1", isActive=1)
        result = await dict_service.create_dictionary(dto)
        assert result.name == "child"

    @pytest.mark.asyncio
    async def test_create_dictionary_parent_not_found(self, dict_service, mock_dict_repo):
        """测试创建字典时父字典不存在。"""
        mock_dict_repo.get_by_id = AsyncMock(return_value=None)

        dto = DictionaryCreateDTO(name="child", parentId="non-existent", isActive=1)
        with pytest.raises(BusinessError) as exc_info:
            await dict_service.create_dictionary(dto)
        assert "父字典" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_dictionary_auto_sort(self, dict_service, mock_dict_repo):
        """测试创建字典时自动排序。"""
        mock_dict_repo.get_max_sort = AsyncMock(return_value=5)
        created = DictionaryEntity(id="1", name="test", sort=6)
        mock_dict_repo.create = AsyncMock(return_value=created)

        dto = DictionaryCreateDTO(name="test", label="测试", isActive=1)
        await dict_service.create_dictionary(dto)
        # 验证传给 create 的实体 sort 值为 max_sort + 1
        call_args = mock_dict_repo.create.call_args[0][0]
        assert call_args.sort == 6

    @pytest.mark.asyncio
    async def test_update_dictionary_success(self, dict_service, mock_dict_repo):
        """测试更新字典成功。"""
        existing = DictionaryEntity(id="1", name="old", label="旧")
        updated = DictionaryEntity(id="1", name="new", label="新")
        mock_dict_repo.get_by_id = AsyncMock(side_effect=[existing, updated])
        mock_dict_repo.update = AsyncMock(return_value=updated)

        dto = DictionaryUpdateDTO(name="new", label="新")
        result = await dict_service.update_dictionary("1", dto)
        assert result.name == "new"

    @pytest.mark.asyncio
    async def test_update_dictionary_not_found(self, dict_service, mock_dict_repo):
        """测试更新不存在的字典。"""
        mock_dict_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await dict_service.update_dictionary("non-existent", DictionaryUpdateDTO(name="new"))

    @pytest.mark.asyncio
    async def test_update_dictionary_circular_reference(self, dict_service, mock_dict_repo):
        """测试更新字典时循环引用。"""
        d = DictionaryEntity(id="dict-1", name="测试")
        mock_dict_repo.get_by_id = AsyncMock(return_value=d)

        dto = DictionaryUpdateDTO(parentId="dict-1")
        with pytest.raises(BusinessError) as exc_info:
            await dict_service.update_dictionary("dict-1", dto)
        assert "自己" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_dictionary_success(self, dict_service, mock_dict_repo):
        """测试删除字典成功。"""
        d = DictionaryEntity(id="1", name="test")
        mock_dict_repo.get_by_id = AsyncMock(return_value=d)
        mock_dict_repo.get_by_parent_id = AsyncMock(return_value=[])
        mock_dict_repo.delete = AsyncMock(return_value=True)

        result = await dict_service.delete_dictionary("1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_dictionary_not_found(self, dict_service, mock_dict_repo):
        """测试删除不存在的字典。"""
        mock_dict_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await dict_service.delete_dictionary("non-existent")

    @pytest.mark.asyncio
    async def test_delete_dictionary_with_children(self, dict_service, mock_dict_repo):
        """测试删除有子字典的字典。"""
        d = DictionaryEntity(id="1", name="parent")
        child = DictionaryEntity(id="2", name="child", parent_id="1")
        mock_dict_repo.get_by_id = AsyncMock(return_value=d)
        mock_dict_repo.get_by_parent_id = AsyncMock(return_value=[child])

        with pytest.raises(BusinessError) as exc_info:
            await dict_service.delete_dictionary("1")
        assert "子字典" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_dictionary_by_name_empty(self, dict_service, mock_dict_repo):
        """测试按名称查询字典返回空。"""
        mock_dict_repo.get_filtered = AsyncMock(return_value=[])
        result = await dict_service.get_dictionary_by_name("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_create_dictionary_with_custom_sort(self, dict_service, mock_dict_repo):
        """测试创建字典时指定自定义排序。"""
        created = DictionaryEntity(id="1", name="status", label="状态", value="1", sort=99)
        mock_dict_repo.create = AsyncMock(return_value=created)

        dto = DictionaryCreateDTO(name="status", label="状态", value="1", sort=99, isActive=1)
        result = await dict_service.create_dictionary(dto)
        assert result.name == "status"
        assert result.sort == 99

    @pytest.mark.asyncio
    async def test_create_dictionary_auto_sort_root(self, dict_service, mock_dict_repo):
        """测试创建字典时自动排序（根级，parent_id=None）。"""
        mock_dict_repo.get_max_sort = AsyncMock(return_value=0)
        created = DictionaryEntity(id="1", name="test", sort=1)
        mock_dict_repo.create = AsyncMock(return_value=created)

        dto = DictionaryCreateDTO(name="test", label="测试", isActive=1)
        await dict_service.create_dictionary(dto)
        call_args = mock_dict_repo.create.call_args[0][0]
        assert call_args.sort == 1

    @pytest.mark.asyncio
    async def test_update_dictionary_parent_id_cleared(self, dict_service, mock_dict_repo):
        """测试更新字典时清除 parentId。"""
        d = DictionaryEntity(id="1", name="test", parent_id="parent-1")
        updated = DictionaryEntity(id="1", name="test", parent_id=None)
        mock_dict_repo.get_by_id = AsyncMock(side_effect=[d, updated])
        mock_dict_repo.update = AsyncMock(return_value=updated)

        dto = DictionaryUpdateDTO(parentId="")
        result = await dict_service.update_dictionary("1", dto)
        assert result.parentId is None

    @pytest.mark.asyncio
    async def test_update_dictionary_parent_not_found(self, dict_service, mock_dict_repo):
        """测试更新字典时父字典不存在。"""
        d = DictionaryEntity(id="1", name="test")
        mock_dict_repo.get_by_id = AsyncMock(side_effect=[d, None])

        dto = DictionaryUpdateDTO(parentId="non-existent")
        with pytest.raises(BusinessError) as exc_info:
            await dict_service.update_dictionary("1", dto)
        assert "父字典" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_dictionary_all_fields(self, dict_service, mock_dict_repo):
        """测试更新字典所有字段。"""
        existing = DictionaryEntity(id="1", name="old", label="旧标签", value="0", sort=1, is_active=1)
        updated = DictionaryEntity(id="1", name="new", label="新标签", value="1", sort=2, is_active=0)
        mock_dict_repo.get_by_id = AsyncMock(side_effect=[existing, updated])
        mock_dict_repo.update = AsyncMock(return_value=updated)

        dto = DictionaryUpdateDTO(name="new", label="新标签", value="1", sort=2, isActive=0)
        result = await dict_service.update_dictionary("1", dto)
        assert result.name == "new"
        assert result.label == "新标签"
        assert result.isActive == 0

    def test_to_response(self, dict_service):
        """测试 _to_response 静态方法。"""
        from datetime import datetime
        now = datetime.now()
        d = DictionaryEntity(
            id="1",
            name="status",
            label="状态",
            value="1",
            sort=1,
            is_active=1,
            parent_id="0",
            created_time=now,
            updated_time=now,
            description="描述",
        )
        result = dict_service._to_response(d)
        assert result.id == "1"
        assert result.name == "status"
        assert result.label == "状态"
        assert result.value == "1"
        assert result.sort == 1
        assert result.isActive == 1
        assert result.parentId == "0"
        assert result.description == "描述"
