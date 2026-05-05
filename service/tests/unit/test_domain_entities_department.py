"""部门领域实体的单元测试。

测试 DepartmentEntity 的状态查询属性、业务规则方法和工厂方法。
"""

import pytest

from src.domain.entities.department import DepartmentEntity


@pytest.mark.unit
class TestDepartmentEntity:
    """DepartmentEntity 测试类。"""

    # ---- 状态查询属性测试 ----

    def test_is_active_dept_when_active(self):
        """测试 is_active_dept 属性（已启用）。"""
        dept = DepartmentEntity(id="dept-1", name="技术部", code="tech", is_active=1)
        assert dept.is_active_dept is True

    def test_is_active_dept_when_inactive(self):
        """测试 is_active_dept 属性（未启用）。"""
        dept = DepartmentEntity(id="dept-1", name="技术部", code="tech", is_active=0)
        assert dept.is_active_dept is False

    # ---- 业务规则方法测试 ----

    def test_is_circular_reference_true(self):
        """测试 is_circular_reference 方法（自身引用）。"""
        dept = DepartmentEntity(id="dept-1", name="技术部", code="tech")
        assert dept.is_circular_reference("dept-1") is True

    def test_is_circular_reference_different_parent(self):
        """测试 is_circular_reference 方法（不同父节点）。"""
        dept = DepartmentEntity(id="dept-1", name="技术部", code="tech")
        assert dept.is_circular_reference("dept-2") is False

    def test_is_circular_reference_none(self):
        """测试 is_circular_reference 方法（无父节点）。"""
        dept = DepartmentEntity(id="dept-1", name="技术部", code="tech")
        assert dept.is_circular_reference(None) is False

    # ---- 状态变更方法测试 ----

    def test_update_info_with_all_fields(self):
        """测试 update_info 方法（更新所有字段）。"""
        dept = DepartmentEntity(id="dept-1", name="技术部", code="tech", mode_type=0, rank=1)
        dept.update_info(
            name="研发部",
            code="rd",
            mode_type=1,
            rank=2,
            auto_bind=1,
            parent_id="parent-1",
            description="描述",
        )
        assert dept.name == "研发部"
        assert dept.code == "rd"
        assert dept.mode_type == 1
        assert dept.rank == 2
        assert dept.auto_bind == 1
        assert dept.parent_id == "parent-1"
        assert dept.description == "描述"

    def test_update_info_with_partial_fields(self):
        """测试 update_info 方法（部分字段）。"""
        dept = DepartmentEntity(id="dept-1", name="技术部", code="tech")
        dept.update_info(name="新部门", rank=5)
        assert dept.name == "新部门"
        assert dept.rank == 5
        assert dept.code == "tech"

    def test_update_info_ignore_none_fields(self):
        """测试 update_info 方法（忽略 None 字段）。"""
        dept = DepartmentEntity(id="dept-1", name="技术部", code="tech", rank=1)
        dept.update_info(name=None, rank=None)
        assert dept.name == "技术部"
        assert dept.rank == 1

    # ---- 工厂方法测试 ----

    def test_create_new(self):
        """测试 create_new 工厂方法。"""
        dept = DepartmentEntity.create_new(
            name="技术部",
            code="tech",
            parent_id="parent-1",
            mode_type=1,
            rank=2,
            auto_bind=1,
            description="技术部门",
        )
        assert dept.id is not None
        assert len(dept.id) == 32
        assert dept.name == "技术部"
        assert dept.code == "tech"
        assert dept.parent_id == "parent-1"
        assert dept.mode_type == 1
        assert dept.rank == 2
        assert dept.auto_bind == 1
        assert dept.description == "技术部门"

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        dept = DepartmentEntity.create_new(name="财务部")
        assert dept.name == "财务部"
        assert dept.code == ""
        assert dept.mode_type == 0
        assert dept.rank == 0
        assert dept.auto_bind == 0
        assert dept.parent_id is None
