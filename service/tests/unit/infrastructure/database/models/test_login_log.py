"""LoginLog 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.login_log import LoginLog


@pytest.mark.unit
class TestLoginLogModel:
    """LoginLog ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_userloginlog。"""
        assert LoginLog.__tablename__ == "sys_userloginlog"

    def test_is_sqlmodel_table(self):
        """LoginLog 应继承 SQLModel 并映射为表。"""
        assert issubclass(LoginLog, SQLModel)
        assert hasattr(LoginLog, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        log = LoginLog()
        assert log.id is not None
        assert len(log.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        log = LoginLog()
        assert log.status == 1
        assert log.login_type == 0

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        log = LoginLog()
        assert log.ipaddress is None
        assert log.browser is None
        assert log.system is None
        assert log.agent is None
        assert log.creator_id is None
        assert log.modifier_id is None
        assert log.created_time is None
        assert log.updated_time is None
        assert log.description is None

    def test_field_max_length(self):
        """字段应有正确的 max_length 限制。"""
        assert LoginLog.ipaddress.type.length == 39
        assert LoginLog.browser.type.length == 64
        assert LoginLog.system.type.length == 64
        assert LoginLog.agent.type.length == 128
        assert LoginLog.creator_id.type.length == 150
        assert LoginLog.modifier_id.type.length == 150
        assert LoginLog.description.type.length == 256

    def test_to_domain(self):
        """to_domain 应返回 LoginLogEntity 实例。"""
        from src.domain.entities.log import LoginLogEntity

        log = LoginLog(
            id="log-1",
            status=1,
            ipaddress="192.168.1.1",
            browser="Chrome",
            system="Windows",
            agent="Mozilla/5.0",
            login_type=0,
        )
        entity = log.to_domain()
        assert isinstance(entity, LoginLogEntity)
        assert entity.id == "log-1"
        assert entity.status == 1
        assert entity.ipaddress == "192.168.1.1"
        assert entity.browser == "Chrome"
        assert entity.system == "Windows"
        assert entity.agent == "Mozilla/5.0"
        assert entity.login_type == 0

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.log import LoginLogEntity

        entity = LoginLogEntity(
            id="log-2", status=0, ipaddress="10.0.0.1", browser="Firefox", system="Linux", agent="Gecko", login_type=1
        )
        log = LoginLog.from_domain(entity)
        assert isinstance(log, LoginLog)
        assert log.id == "log-2"
        assert log.status == 0
        assert log.ipaddress == "10.0.0.1"
        assert log.browser == "Firefox"
        assert log.login_type == 1

    def test_repr(self):
        """__repr__ 应包含 id 和 status。"""
        log = LoginLog()
        log.id = "log-123"
        log.status = 1
        r = repr(log)
        assert "LoginLog" in r
        assert "log-123" in r
        assert "1" in r
