"""仓储层 _build_update_values 的单元测试。

回归背景：MenuRepository.update_meta 曾用仓储自身的 ``_model_class``（Menu）
去过滤 MenuMeta 实体的字段，``title``/``icon`` 等被整体丢弃、UPDATE 只剩审计列
甚至空转 —— 表现为「菜单编辑后标题/图标不改」，且原始 SQL 可证未落库。
"""

from typing import cast
from unittest.mock import MagicMock

import pytest

from src.domain.entities.menu_meta import MenuMetaEntity
from src.infrastructure.database.models.menu import Menu
from src.infrastructure.database.models.menu_meta import MenuMeta
from src.infrastructure.repositories.menu_repository import MenuRepository
from sqlmodel.ext.asyncio.session import AsyncSession


def _repo() -> MenuRepository:
    """仅调用 _build_update_values，不需要真实 session。"""
    return MenuRepository(session=cast(AsyncSession, MagicMock()))


@pytest.mark.unit
class TestBuildUpdateValues:
    def test_menu_meta_values_include_display_fields(self) -> None:
        """更新 MenuMeta 必须显式传 model_class=MenuMeta，否则字段被整表过滤。"""
        meta = MenuMetaEntity.create_new(
            title="用户管理",
            icon="ri:user-line",
            is_show_menu=0,
            is_keepalive=1,
            frame_url="https://example.com",
            transition_enter="animate__fadeIn",
        )
        values = _repo()._build_update_values(
            meta,
            model_class=MenuMeta,
            exclude=("id", "created_time", "updated_time", "creator_id", "modifier_id"),
        )
        assert values["title"] == "用户管理"
        assert values["icon"] == "ri:user-line"
        assert values["is_show_menu"] == 0
        assert values["is_keepalive"] == 1
        assert values["frame_url"] == "https://example.com"
        assert values["transition_enter"] == "animate__fadeIn"
        # 主键与审计列不应出现在 SET 子句里
        for excluded in ("id", "created_time", "updated_time", "creator_id", "modifier_id"):
            assert excluded not in values

    def test_default_model_class_filters_by_repo_model(self) -> None:
        """不传 model_class 时仍按仓储自身模型（Menu）过滤 —— 用于固化契约。"""
        meta = MenuMetaEntity.create_new(title="用户管理")
        values = _repo()._build_update_values(meta)
        # Menu 表没有 title 列，故被过滤掉（这正是当年 update_meta 空转的原因）
        assert "title" not in values
        assert "icon" not in values

    def test_menu_entity_values_use_menu_columns(self) -> None:
        """Menu 实体走默认模型类，业务列齐全。"""
        from src.domain.entities.menu import MenuEntity

        menu = MenuEntity.create_new(
            name="user_mgr",
            menu_type=1,
            path="/system/user",
            component="system/user/index",
            rank=10,
            is_active=1,
        )
        values = _repo()._build_update_values(menu)
        assert values["name"] == "user_mgr"
        assert values["path"] == "/system/user"
        assert values["rank"] == 10
        assert "id" not in values
