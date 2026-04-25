"""菜单元数据领域实体的单元测试。

测试 MenuMetaEntity 的状态变更方法和工厂方法。
"""

import pytest

from src.domain.entities.menu_meta import MenuMetaEntity


@pytest.mark.unit
class TestMenuMetaEntity:
    """MenuMetaEntity 测试类。"""

    # ---- 状态变更方法测试 ----

    def test_update_info_with_all_fields(self):
        """测试 update_info 方法（更新所有字段）。"""
        meta = MenuMetaEntity(id="meta-1", title="首页")
        meta.update_info(
            title="用户管理",
            icon="user-icon",
            r_svg_name="ri-user-line",
            is_show_menu=1,
            is_show_parent=1,
            is_keepalive=1,
            frame_url="http://example.com",
            frame_loading=1,
            transition_enter="fade",
            transition_leave="slide",
            is_hidden_tag=1,
            fixed_tag=1,
            dynamic_level=2,
            description="描述",
        )
        assert meta.title == "用户管理"
        assert meta.icon == "user-icon"
        assert meta.r_svg_name == "ri-user-line"
        assert meta.is_show_menu == 1
        assert meta.is_show_parent == 1
        assert meta.is_keepalive == 1
        assert meta.frame_url == "http://example.com"
        assert meta.frame_loading == 1
        assert meta.transition_enter == "fade"
        assert meta.transition_leave == "slide"
        assert meta.is_hidden_tag == 1
        assert meta.fixed_tag == 1
        assert meta.dynamic_level == 2
        assert meta.description == "描述"

    def test_update_info_with_partial_fields(self):
        """测试 update_info 方法（部分字段）。"""
        meta = MenuMetaEntity(id="meta-1", title="首页")
        meta.update_info(title="新标题", icon="new-icon")
        assert meta.title == "新标题"
        assert meta.icon == "new-icon"

    def test_update_info_ignore_none_fields(self):
        """测试 update_info 方法（忽略 None 字段）。"""
        meta = MenuMetaEntity(id="meta-1", title="首页", icon="old-icon")
        meta.update_info(title=None, icon=None)
        assert meta.title == "首页"
        assert meta.icon == "old-icon"

    # ---- 工厂方法测试 ----

    def test_create_new(self):
        """测试 create_new 工厂方法。"""
        meta = MenuMetaEntity.create_new(
            title="用户管理",
            icon="user-icon",
            r_svg_name="ri-user-line",
            is_show_menu=1,
            is_show_parent=1,
            is_keepalive=1,
            frame_url="http://example.com",
            frame_loading=1,
            transition_enter="fade",
            transition_leave="slide",
            is_hidden_tag=1,
            fixed_tag=1,
            dynamic_level=2,
        )
        assert meta.id is not None
        assert len(meta.id) == 32
        assert meta.title == "用户管理"
        assert meta.icon == "user-icon"
        assert meta.r_svg_name == "ri-user-line"
        assert meta.is_show_menu == 1
        assert meta.is_show_parent == 1
        assert meta.is_keepalive == 1
        assert meta.frame_url == "http://example.com"
        assert meta.frame_loading == 1
        assert meta.transition_enter == "fade"
        assert meta.transition_leave == "slide"
        assert meta.is_hidden_tag == 1
        assert meta.fixed_tag == 1
        assert meta.dynamic_level == 2

    def test_create_new_with_defaults(self):
        """测试 create_new 工厂方法（使用默认值）。"""
        meta = MenuMetaEntity.create_new(title="首页")
        assert meta.title == "首页"
        assert meta.icon == ""
        assert meta.r_svg_name == ""
        assert meta.is_show_menu == 1
        assert meta.is_show_parent == 0
        assert meta.is_keepalive == 0
        assert meta.is_hidden_tag == 0
        assert meta.fixed_tag == 0
        assert meta.dynamic_level == 0
