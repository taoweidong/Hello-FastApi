"""Dictionary 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.dictionary import Dictionary


@pytest.mark.unit
class TestDictionaryModel:
    """Dictionary ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_dictionary。"""
        assert Dictionary.__tablename__ == "sys_dictionary"

    def test_is_sqlmodel_table(self):
        """Dictionary 应继承 SQLModel 并映射为表。"""
        assert issubclass(Dictionary, SQLModel)
        assert hasattr(Dictionary, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        d = Dictionary(name="测试字典")
        assert d.id is not None
        assert len(d.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        d = Dictionary(name="测试字典")
        assert d.label == ""
        assert d.value == ""
        assert d.sort == 0
        assert d.is_active == 1

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        d = Dictionary(name="测试字典")
        assert d.parent_id is None
        assert d.description is None
        assert d.created_time is None
        assert d.updated_time is None

    def test_column_type_length(self):
        """字段应有正确的类型长度限制。"""
        assert Dictionary.__table__.columns["name"].type.length == 128
        assert Dictionary.__table__.columns["label"].type.length == 128
        assert Dictionary.__table__.columns["value"].type.length == 128

    def test_to_domain(self):
        """to_domain 应返回 DictionaryEntity 实例。"""
        from src.domain.entities.dictionary import DictionaryEntity

        d = Dictionary(id="dict-1", name="状态", label="启用", value="1", sort=1, is_active=1)
        entity = d.to_domain()
        assert isinstance(entity, DictionaryEntity)
        assert entity.id == "dict-1"
        assert entity.name == "状态"
        assert entity.label == "启用"
        assert entity.value == "1"
        assert entity.sort == 1

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.dictionary import DictionaryEntity

        entity = DictionaryEntity(id="dict-2", name="类型", label="禁用", value="0", sort=2, is_active=0)
        d = Dictionary.from_domain(entity)
        assert isinstance(d, Dictionary)
        assert d.id == "dict-2"
        assert d.name == "类型"
        assert d.label == "禁用"
        assert d.value == "0"
        assert d.sort == 2
        assert d.is_active == 0

    def test_repr(self):
        """__repr__ 应包含 id 和 name。"""
        d = Dictionary(name="测试")
        d.id = "dict-123"
        r = repr(d)
        assert "Dictionary" in r
        assert "dict-123" in r
        assert "测试" in r

    def test_parent_id_self_reference_fk(self):
        """parent_id 应自引用 sys_dictionary.id。"""
        fks = Dictionary.parent_id.foreign_keys
        assert len(fks) > 0
        fk = next(iter(fks))
        assert "sys_dictionary.id" in str(fk.target_fullname)
