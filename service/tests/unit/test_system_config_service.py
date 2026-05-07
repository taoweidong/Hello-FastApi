"""系统配置服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.system_config_dto import SystemConfigCreateDTO, SystemConfigListQueryDTO, SystemConfigUpdateDTO
from src.application.services.system_config_service import SystemConfigService
from src.domain.entities.system_config import SystemConfigEntity
from src.domain.exceptions import ConflictError, NotFoundError


@pytest.mark.unit
class TestSystemConfigService:
    """SystemConfigService 测试类。"""

    @pytest.fixture
    def mock_config_repo(self):
        """创建模拟系统配置仓储。"""
        repo = AsyncMock()
        repo.get_by_key = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock(return_value=False)
        repo.count = AsyncMock(return_value=0)
        repo.get_all = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def config_service(self, mock_config_repo):
        """创建系统配置服务实例。"""
        return SystemConfigService(config_repo=mock_config_repo)

    @pytest.mark.asyncio
    async def test_create_config_success(self, config_service, mock_config_repo):
        """测试创建配置成功。"""
        created_config = SystemConfigEntity(id="config-id-1", key="site_name", value="测试站点", is_active=1)
        mock_config_repo.get_by_key = AsyncMock(return_value=None)
        mock_config_repo.create = AsyncMock(return_value=created_config)

        dto = SystemConfigCreateDTO(key="site_name", value="测试站点", isActive=1)
        result = await config_service.create_config(dto)

        assert result.key == "site_name"
        assert result.value == "测试站点"

    @pytest.mark.asyncio
    async def test_create_config_duplicate_key(self, config_service, mock_config_repo):
        """测试创建配置时key重复。"""
        existing = SystemConfigEntity(id="ex-id", key="site_name")
        mock_config_repo.get_by_key = AsyncMock(return_value=existing)

        dto = SystemConfigCreateDTO(key="site_name", value="新值")
        with pytest.raises(ConflictError) as exc_info:
            await config_service.create_config(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_config_not_found(self, config_service, mock_config_repo):
        """测试获取不存在的配置。"""
        mock_config_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await config_service.get_config("non-existent-id")

    @pytest.mark.asyncio
    async def test_get_configs_with_pagination(self, config_service, mock_config_repo):
        """测试获取配置列表（分页+筛选）。"""
        configs = [
            SystemConfigEntity(id="1", key="site_name", value="站点A", is_active=1),
            SystemConfigEntity(id="2", key="site_desc", value="描述", is_active=1),
        ]
        mock_config_repo.count = AsyncMock(return_value=2)
        mock_config_repo.get_all = AsyncMock(return_value=configs)

        query = SystemConfigListQueryDTO(pageNum=1, pageSize=10)
        results, total = await config_service.get_configs(query)

        assert total == 2
        assert len(results) == 2
        mock_config_repo.count.assert_called_once()
        mock_config_repo.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_config_success(self, config_service, mock_config_repo):
        """测试更新配置成功。"""
        existing_config = SystemConfigEntity(id="config-id-1", key="site_name", value="旧值", is_active=1)
        updated_config = SystemConfigEntity(id="config-id-1", key="site_name", value="新值", is_active=1)
        mock_config_repo.get_by_id = AsyncMock(return_value=existing_config)
        mock_config_repo.update = AsyncMock(return_value=updated_config)

        dto = SystemConfigUpdateDTO(value="新值")
        result = await config_service.update_config("config-id-1", dto)

        assert result.value == "新值"
        mock_config_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_config_not_found(self, config_service, mock_config_repo):
        """测试更新不存在的配置。"""
        mock_config_repo.get_by_id = AsyncMock(return_value=None)

        dto = SystemConfigUpdateDTO(value="新值")
        with pytest.raises(NotFoundError):
            await config_service.update_config("non-existent-id", dto)

    @pytest.mark.asyncio
    async def test_update_config_duplicate_key(self, config_service, mock_config_repo):
        """测试更新配置时key与其他配置重复。"""
        existing_config = SystemConfigEntity(id="config-id-1", key="site_name", value="旧值")
        other_config = SystemConfigEntity(id="config-id-2", key="other_key")
        mock_config_repo.get_by_id = AsyncMock(return_value=existing_config)
        mock_config_repo.get_by_key = AsyncMock(return_value=other_config)

        dto = SystemConfigUpdateDTO(key="other_key")
        with pytest.raises(ConflictError):
            await config_service.update_config("config-id-1", dto)

    @pytest.mark.asyncio
    async def test_delete_config_success(self, config_service, mock_config_repo):
        """测试删除配置成功。"""
        mock_config_repo.delete = AsyncMock(return_value=True)

        result = await config_service.delete_config("config-id-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self, config_service, mock_config_repo):
        """测试删除不存在的配置。"""
        mock_config_repo.delete = AsyncMock(return_value=False)

        with pytest.raises(NotFoundError):
            await config_service.delete_config("non-existent-id")

    @pytest.mark.asyncio
    async def test_create_config_with_optional_fields(self, config_service, mock_config_repo):
        """测试创建配置包含所有可选字段。"""
        created = SystemConfigEntity(id="cfg-1", key="test_key", value="test_val", is_active=0, access=2, inherit=1)
        mock_config_repo.get_by_key = AsyncMock(return_value=None)
        mock_config_repo.create = AsyncMock(return_value=created)

        dto = SystemConfigCreateDTO(key="test_key", value="test_val", isActive=0, access=2, inherit=1)
        result = await config_service.create_config(dto)
        assert result.key == "test_key"
        assert result.value == "test_val"
        assert result.isActive == 0
        assert result.access == 2
        assert result.inherit == 1

    @pytest.mark.asyncio
    async def test_get_config_success(self, config_service, mock_config_repo):
        """测试获取配置成功。"""
        config = SystemConfigEntity(id="cfg-1", key="site_name", value="测试站点", is_active=1)
        mock_config_repo.get_by_id = AsyncMock(return_value=config)

        result = await config_service.get_config("cfg-1")
        assert result.id == "cfg-1"
        assert result.key == "site_name"
        assert result.value == "测试站点"

    @pytest.mark.asyncio
    async def test_get_configs_with_filters(self, config_service, mock_config_repo):
        """测试带筛选获取配置列表。"""
        configs = [SystemConfigEntity(id="1", key="site_name", value="站点A", is_active=1)]
        mock_config_repo.count = AsyncMock(return_value=1)
        mock_config_repo.get_all = AsyncMock(return_value=configs)

        query = SystemConfigListQueryDTO(pageNum=1, pageSize=10, key="site", isActive=1)
        results, total = await config_service.get_configs(query)
        assert total == 1
        assert len(results) == 1
        mock_config_repo.count.assert_called_with(key="site", is_active=1)
        mock_config_repo.get_all.assert_called_with(page_num=1, page_size=10, key="site", is_active=1)

    @pytest.mark.asyncio
    async def test_update_config_all_fields(self, config_service, mock_config_repo):
        """测试更新配置所有字段。"""
        existing = SystemConfigEntity(id="cfg-1", key="site_name", value="旧值", is_active=1, access=0, inherit=0)
        updated = SystemConfigEntity(id="cfg-1", key="new_key", value="新值", is_active=0, access=1, inherit=1)
        mock_config_repo.get_by_id = AsyncMock(return_value=existing)
        mock_config_repo.get_by_key = AsyncMock(return_value=None)
        mock_config_repo.update = AsyncMock(return_value=updated)

        dto = SystemConfigUpdateDTO(key="new_key", value="新值", isActive=0, access=1, inherit=1)
        result = await config_service.update_config("cfg-1", dto)
        assert result.key == "new_key"
        assert result.value == "新值"
        assert result.isActive == 0
        assert result.access == 1
        assert result.inherit == 1

    def test_to_response(self, config_service):
        """测试 _to_response 静态方法。"""
        from datetime import datetime
        now = datetime.now()
        config = SystemConfigEntity(
            id="cfg-1",
            key="test_key",
            value="test_val",
            is_active=1,
            access=1,
            inherit=0,
            creator_id="u1",
            modifier_id="u2",
            created_time=now,
            updated_time=now,
            description="测试配置",
        )
        result = config_service._to_response(config)
        assert result.id == "cfg-1"
        assert result.key == "test_key"
        assert result.value == "test_val"
        assert result.isActive == 1
        assert result.access == 1
        assert result.inherit == 0
        assert result.description == "测试配置"
