"""菜单实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.menu import MenuEntity


class Menu(SQLModel, table=True):
    """菜单实体模型。"""

    __tablename__ = "sys_menus"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=64)  # 菜单名称
    path: str | None = Field(default=None, max_length=256)  # 路由路径
    component: str | None = Field(default=None, max_length=256)  # 组件路径
    icon: str | None = Field(default=None, max_length=64)  # 图标
    title: str | None = Field(default=None, max_length=64)  # 显示标题
    show_link: int = Field(default=1)  # 是否显示(0-隐藏, 1-显示)
    parent_id: str | None = Field(default=None, foreign_key="sys_menus.id")  # 父菜单ID
    order_num: int = Field(default=0)  # 排序号
    permissions: str | None = Field(default=None, max_length=500)  # 关联权限编码，逗号分隔
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    # Pure Admin 扩展字段
    menu_type: int = Field(default=0)  # 菜单类型(0-菜单, 1-iframe, 2-外链, 3-按钮)
    redirect: str | None = Field(default=None, max_length=256)  # 重定向路径
    extra_icon: str | None = Field(default=None, max_length=64)  # 菜单名称右侧额外图标
    enter_transition: str | None = Field(default=None, max_length=64)  # 进场动画
    leave_transition: str | None = Field(default=None, max_length=64)  # 离场动画
    active_path: str | None = Field(default=None, max_length=256)  # 激活菜单路径
    frame_src: str | None = Field(default=None, max_length=500)  # iframe链接地址
    frame_loading: bool = Field(default=True)  # iframe首次加载动画
    keep_alive: bool = Field(default=False)  # 是否缓存页面
    hidden_tag: bool = Field(default=False)  # 禁止添加到标签页
    fixed_tag: bool = Field(default=False)  # 固定标签页
    show_parent: bool = Field(default=False)  # 是否显示父级菜单
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    def to_domain(self) -> "MenuEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.menu import MenuEntity

        return MenuEntity(
            id=self.id,
            name=self.name,
            path=self.path,
            component=self.component,
            icon=self.icon,
            title=self.title,
            show_link=self.show_link,
            parent_id=self.parent_id,
            order_num=self.order_num,
            permissions=self.permissions,
            status=self.status,
            menu_type=self.menu_type,
            redirect=self.redirect,
            extra_icon=self.extra_icon,
            enter_transition=self.enter_transition,
            leave_transition=self.leave_transition,
            active_path=self.active_path,
            frame_src=self.frame_src,
            frame_loading=self.frame_loading,
            keep_alive=self.keep_alive,
            hidden_tag=self.hidden_tag,
            fixed_tag=self.fixed_tag,
            show_parent=self.show_parent,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "MenuEntity") -> "Menu":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            name=entity.name,
            path=entity.path,
            component=entity.component,
            icon=entity.icon,
            title=entity.title,
            show_link=entity.show_link,
            parent_id=entity.parent_id,
            order_num=entity.order_num,
            permissions=entity.permissions,
            status=entity.status,
            menu_type=entity.menu_type,
            redirect=entity.redirect,
            extra_icon=entity.extra_icon,
            enter_transition=entity.enter_transition,
            leave_transition=entity.leave_transition,
            active_path=entity.active_path,
            frame_src=entity.frame_src,
            frame_loading=entity.frame_loading,
            keep_alive=entity.keep_alive,
            hidden_tag=entity.hidden_tag,
            fixed_tag=entity.fixed_tag,
            show_parent=entity.show_parent,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def __repr__(self) -> str:
        return f"<Menu(id={self.id}, name={self.name})>"
