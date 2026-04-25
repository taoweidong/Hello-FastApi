"""SystemLog 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.system_log import SystemLog


@pytest.mark.unit
class TestSystemLogModel:
    """SystemLog ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_logs。"""
        assert SystemLog.__tablename__ == "sys_logs"

    def test_is_sqlmodel_table(self):
        """SystemLog 应继承 SQLModel 并映射为表。"""
        assert issubclass(SystemLog, SQLModel)
        assert hasattr(SystemLog, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        log = SystemLog()
        assert log.id is not None
        assert len(log.id) == 32

    def test_optional_fields_default_none(self):
        """所有非主键字段默认应为 None（除无默认值的字段外）。"""
        log = SystemLog()
        assert log.module is None
        assert log.path is None
        assert log.body is None
        assert log.method is None
        assert log.ipaddress is None
        assert log.browser is None
        assert log.system is None
        assert log.response_code is None
        assert log.response_result is None
        assert log.status_code is None
        assert log.creator_id is None
        assert log.modifier_id is None
        assert log.created_time is None
        assert log.updated_time is None
        assert log.description is None

    def test_field_max_length(self):
        """字段应有正确的 max_length 限制。"""
        assert SystemLog.module.type.length == 64
        assert SystemLog.path.type.length == 400
        assert SystemLog.method.type.length == 8
        assert SystemLog.ipaddress.type.length == 39
        assert SystemLog.browser.type.length == 64
        assert SystemLog.system.type.length == 64
        assert SystemLog.creator_id.type.length == 150
        assert SystemLog.modifier_id.type.length == 150
        assert SystemLog.description.type.length == 256

    def test_to_domain(self):
        """to_domain 应返回 OperationLogEntity 实例。"""
        from src.domain.entities.log import OperationLogEntity

        log = SystemLog(
            id="slog-1",
            module="auth",
            path="/api/login",
            method="POST",
            ipaddress="192.168.1.1",
            response_code=200,
            status_code=0,
        )
        entity = log.to_domain()
        assert isinstance(entity, OperationLogEntity)
        assert entity.id == "slog-1"
        assert entity.module == "auth"
        assert entity.path == "/api/login"
        assert entity.method == "POST"
        assert entity.response_code == 200
        assert entity.status_code == 0

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.log import OperationLogEntity

        entity = OperationLogEntity(
            id="slog-2",
            module="system",
            path="/api/config",
            method="GET",
            ipaddress="10.0.0.1",
            response_code=200,
            status_code=0,
        )
        log = SystemLog.from_domain(entity)
        assert isinstance(log, SystemLog)
        assert log.id == "slog-2"
        assert log.module == "system"
        assert log.path == "/api/config"
        assert log.method == "GET"
        assert log.response_code == 200

    def test_repr(self):
        """__repr__ 应包含 id 和 module。"""
        log = SystemLog()
        log.id = "slog-123"
        log.module = "auth"
        r = repr(log)
        assert "SystemLog" in r
        assert "slog-123" in r
        assert "auth" in r
