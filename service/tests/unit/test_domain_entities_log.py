"""日志领域实体的单元测试。

测试 LoginLogEntity 和 OperationLogEntity 的状态查询属性和工厂方法。
"""

import pytest

from src.domain.entities.log import LoginLogEntity, OperationLogEntity


@pytest.mark.unit
class TestLoginLogEntity:
    """LoginLogEntity 测试类。"""

    # ---- 状态查询属性测试 ----

    def test_is_success_when_success(self):
        """测试 is_success 属性（成功）。"""
        log = LoginLogEntity(id="log-1", status=1)
        assert log.is_success is True

    def test_is_success_when_failed(self):
        """测试 is_success 属性（失败）。"""
        log = LoginLogEntity(id="log-1", status=0)
        assert log.is_success is False

    # ---- 工厂方法测试 ----

    def test_create_new_with_all_fields(self):
        """测试 create_new 工厂方法（所有字段）。"""
        log = LoginLogEntity.create_new(
            status=1,
            ipaddress="192.168.1.100",
            browser="Chrome",
            system="Windows 11",
            agent="Mozilla/5.0",
            login_type=0,
            description="登录成功",
        )
        assert log.id is not None
        assert len(log.id) == 32
        assert log.status == 1
        assert log.ipaddress == "192.168.1.100"
        assert log.browser == "Chrome"
        assert log.system == "Windows 11"
        assert log.agent == "Mozilla/5.0"
        assert log.login_type == 0
        assert log.description == "登录成功"

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        log = LoginLogEntity.create_new()
        assert log.status == 1
        assert log.ipaddress is None
        assert log.browser is None
        assert log.login_type == 0


@pytest.mark.unit
class TestOperationLogEntity:
    """OperationLogEntity 测试类。"""

    # ---- 工厂方法测试 ----

    def test_create_new_with_all_fields(self):
        """测试 create_new 工厂方法（所有字段）。"""
        log = OperationLogEntity.create_new(
            module="用户模块",
            path="/api/users",
            method="POST",
            ipaddress="192.168.1.100",
            browser="Chrome",
            system="Windows 11",
            response_code=200,
            response_result='{"id": "1"}',
            status_code=200,
            description="创建用户",
        )
        assert log.id is not None
        assert len(log.id) == 32
        assert log.module == "用户模块"
        assert log.path == "/api/users"
        assert log.method == "POST"
        assert log.ipaddress == "192.168.1.100"
        assert log.browser == "Chrome"
        assert log.system == "Windows 11"
        assert log.response_code == 200
        assert log.response_result == '{"id": "1"}'
        assert log.status_code == 200
        assert log.description == "创建用户"

    def test_create_new_with_partial_fields(self):
        """测试 create_new 工厂方法（部分字段）。"""
        log = OperationLogEntity.create_new(module="用户模块", path="/api/users", method="GET", response_code=200)
        assert log.module == "用户模块"
        assert log.path == "/api/users"
        assert log.method == "GET"
        assert log.response_code == 200

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        log = OperationLogEntity.create_new()
        assert log.module is None
        assert log.path is None
        assert log.method is None
        assert log.response_code is None


@pytest.mark.unit
class TestSystemLogEntityAlias:
    """测试 SystemLogEntity 别名（向后兼容）。"""

    def test_system_log_entity_is_alias(self):
        """测试 SystemLogEntity 是 OperationLogEntity 的别名。"""
        from src.domain.entities.log import SystemLogEntity

        assert SystemLogEntity is OperationLogEntity
