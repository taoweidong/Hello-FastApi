"""MenuMeta 模型单元测试。

测试表结构、字段类型、默认值、to_domain/from_domain 转换及 __repr__ 方法。
"""

import pytest
from sqlmodel import SQLModel

from src.infrastructure.database.models.menu_meta import MenuMeta


@pytest.mark.unit
class TestMenuMetaModel:
    """MenuMeta ORM 模型测试类。"""

    def test_table_name(self):
        """表名应为 sys_menumeta。"""
        assert MenuMeta.__tablename__ == "sys_menumeta"

    def test_is_sqlmodel_table(self):
        """MenuMeta 应继承 SQLModel 并映射为表。"""
        assert issubclass(MenuMeta, SQLModel)
        assert hasattr(MenuMeta, "__tablename__")

    def test_id_default_uuid(self):
        """id 字段应有 UUID 默认值工厂。"""
        meta = MenuMeta()
        assert meta.id is not None
        assert len(meta.id) == 32

    def test_field_defaults(self):
        """测试字段默认值。"""
        meta = MenuMeta()
        assert meta.is_show_menu == 1
        assert meta.is_show_parent == 0
        assert meta.is_keepalive == 0
        assert meta.frame_loading == 1
        assert meta.is_hidden_tag == 0
        assert meta.fixed_tag == 0
        assert meta.dynamic_level == 0

    def test_optional_fields_default_none(self):
        """可选字段默认应为 None。"""
        meta = MenuMeta()
        assert meta.title is None
        assert meta.icon is None
        assert meta.r_svg_name is None
        assert meta.frame_url is None
        assert meta.transition_enter is None
        assert meta.transition_leave is None
        assert meta.creator_id is None
        assert meta.modifier_id is None
        assert meta.created_time is None
        assert meta.updated_time is None
        assert meta.description is None

    def test_field_max_length(self):
        """字段应有正确的 max_length 限制。"""
        assert MenuMeta.title.type.length == 255
        assert MenuMeta.icon.type.length == 255
        assert MenuMeta.r_svg_name.type.length == 255
        assert MenuMeta.frame_url.type.length == 255
        assert MenuMeta.transition_enter.type.length == 255
        assert MenuMeta.transition_leave.type.length == 255
        assert MenuMeta.creator_id.type.length == 150
        assert MenuMeta.modifier_id.type.length == 150
        assert MenuMeta.description.type.length == 256

    def test_to_domain(self):
        """to_domain 应返回 MenuMetaEntity 实例。"""
        from src.domain.entities.menu_meta import MenuMetaEntity

        meta = MenuMeta(
            id="meta-1", title="用户管理", icon="user-icon", r_svg_name="user-line", is_show_menu=1, is_keepalive=1
        )
        entity = meta.to_domain()
        assert isinstance(entity, MenuMetaEntity)
        assert entity.id == "meta-1"
        assert entity.title == "用户管理"
        assert entity.icon == "user-icon"
        assert entity.r_svg_name == "user-line"
        assert entity.is_show_menu == 1
        assert entity.is_keepalive == 1

    def test_from_domain(self):
        """from_domain 应从领域实体创建 ORM 实例。"""
        from src.domain.entities.menu_meta import MenuMetaEntity

        entity = MenuMetaEntity(id="meta-2", title="角色管理", icon="role-icon", is_show_menu=0, is_keepalive=0)
        meta = MenuMeta.from_domain(entity)
        assert isinstance(meta, MenuMeta)
        assert meta.id == "meta-2"
        assert meta.title == "角色管理"
        assert meta.icon == "role-icon"
        assert meta.is_show_menu == 0
        assert meta.is_keepalive == 0

    def test_repr(self):
        """__repr__ 应包含 id 和 title。"""
        meta = MenuMeta()
        meta.id = "meta-123"
        meta.title = "测试元数据"
        r = repr(meta)
        assert "MenuMeta" in r
        assert "meta-123" in r
        assert "测试元数据" in r
