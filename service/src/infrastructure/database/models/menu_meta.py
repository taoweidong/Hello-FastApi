"""菜单元数据实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.menu_meta import MenuMetaEntity


class MenuMeta(SQLModel, table=True):
    """菜单元数据实体（显示配置）。"""

    __tablename__ = "sys_menumeta"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    title: str | None = Field(default=None, max_length=255)  # 菜单显示标题
    icon: str | None = Field(default=None, max_length=255)  # 菜单图标
    r_svg_name: str | None = Field(default=None, max_length=255)  # SVG图标名称(remix icon)
    is_show_menu: int = Field(default=1)  # 是否在菜单中显示(0-隐藏, 1-显示)
    is_show_parent: int = Field(default=0)  # 是否显示父级菜单
    is_keepalive: int = Field(default=0)  # 是否缓存页面(keep-alive)
    frame_url: str | None = Field(default=None, max_length=255)  # iframe内嵌链接
    frame_loading: int = Field(default=1)  # iframe加载动画
    transition_enter: str | None = Field(default=None, max_length=255)  # 进场动画名称
    transition_leave: str | None = Field(default=None, max_length=255)  # 离场动画名称
    is_hidden_tag: int = Field(default=0)  # 禁止添加到标签页
    fixed_tag: int = Field(default=0)  # 固定标签页
    dynamic_level: int = Field(default=0)  # 动态路由层级
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now())
    )
    description: str | None = Field(default=None, max_length=256)

    # 关系 - 被Menu通过meta_id引用
    menu: "Menu" = Relationship(back_populates="meta", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})  # noqa: F821

    def to_domain(self) -> "MenuMetaEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.menu_meta import MenuMetaEntity

        return MenuMetaEntity(
            id=self.id,
            title=self.title,
            icon=self.icon,
            r_svg_name=self.r_svg_name,
            is_show_menu=self.is_show_menu,
            is_show_parent=self.is_show_parent,
            is_keepalive=self.is_keepalive,
            frame_url=self.frame_url,
            frame_loading=self.frame_loading,
            transition_enter=self.transition_enter,
            transition_leave=self.transition_leave,
            is_hidden_tag=self.is_hidden_tag,
            fixed_tag=self.fixed_tag,
            dynamic_level=self.dynamic_level,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "MenuMetaEntity") -> "MenuMeta":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            title=entity.title,
            icon=entity.icon,
            r_svg_name=entity.r_svg_name,
            is_show_menu=entity.is_show_menu,
            is_show_parent=entity.is_show_parent,
            is_keepalive=entity.is_keepalive,
            frame_url=entity.frame_url,
            frame_loading=entity.frame_loading,
            transition_enter=entity.transition_enter,
            transition_leave=entity.transition_leave,
            is_hidden_tag=entity.is_hidden_tag,
            fixed_tag=entity.fixed_tag,
            dynamic_level=entity.dynamic_level,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<MenuMeta(id={self.id}, title={self.title})>"
