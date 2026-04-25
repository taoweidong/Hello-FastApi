"""Department 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.department import Department


@pytest.mark.unit
class TestDepartmentModel:
    """Department ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_departments。"""
        assert Department.__tablename__ == "sys_departments"

    def test_is_sqlmodel_table(self):
        """Department 应继承 SQLModel 并映射为表。"""
        assert issubclass(Department, SQLModel)
        assert hasattr(Department, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        dept = Department(name="测试部门", code="test_dept")
        assert dept.id is not None
        assert len(dept.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        dept = Department(name="测试部门", code="test_dept")
        assert dept.mode_type == 0
        assert dept.rank == 0
        assert dept.auto_bind == 0
        assert dept.is_active == 1

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        dept = Department(name="测试部门", code="test_dept")
        assert dept.creator_id is None
        assert dept.modifier_id is None
        assert dept.parent_id is None
        assert dept.created_time is None
        assert dept.updated_time is None
        assert dept.description is None

    def test_column_type_length(self):
        """字段应有正确的类型长度限制。"""
        assert Department.__table__.columns["id"].type.length == 32
        assert Department.__table__.columns["name"].type.length == 128
        assert Department.__table__.columns["code"].type.length == 128

    def test_to_domain(self):
        """to_domain 应返回 DepartmentEntity 实例。"""
        from src.domain.entities.department import DepartmentEntity

        dept = Department(
            id="dept-1",
            name="研发部",
            code="rd",
            mode_type=0,
            rank=1,
            auto_bind=0,
            is_active=1,
            parent_id=None,
            description="研发部门",
        )
        entity = dept.to_domain()
        assert isinstance(entity, DepartmentEntity)
        assert entity.id == "dept-1"
        assert entity.name == "研发部"
        assert entity.code == "rd"
        assert entity.rank == 1
        assert entity.mode_type == 0

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.department import DepartmentEntity

        entity = DepartmentEntity(id="dept-2", name="市场部", code="mkt", mode_type=1, rank=2, auto_bind=1, is_active=0)
        dept = Department.from_domain(entity)
        assert isinstance(dept, Department)
        assert dept.id == "dept-2"
        assert dept.name == "市场部"
        assert dept.code == "mkt"
        assert dept.mode_type == 1

    def test_repr(self):
        """__repr__ 应包含 id 和 name。"""
        dept = Department(name="测试部", code="test")
        dept.id = "dept-123"
        r = repr(dept)
        assert "Department" in r
        assert "dept-123" in r
        assert "测试部" in r

    def test_code_is_unique(self):
        """code 字段应标记为 unique。"""
        assert Department.code.unique is True

    def test_parent_id_self_reference_fk(self):
        """parent_id 应自引用 sys_departments.id。"""
        fks = Department.parent_id.foreign_keys
        assert len(fks) > 0
        fk = next(iter(fks))
        assert "sys_departments.id" in str(fk.target_fullname)
