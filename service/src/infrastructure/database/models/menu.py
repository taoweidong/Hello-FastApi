"""菜单实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.menu import MenuEntity


class Menu(SQLModel, table=True):
    """菜单实体模型（路由/组件/权限）。"""

    __tablename__ = "sys_menus"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    menu_type: int = Field(default=0)  # 菜单类型(0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限)
    name: str = Field(max_length=128, unique=True)  # 菜单名称(唯一)
    rank: int = Field(default=0)  # 排序号
    path: str = Field(default="", max_length=255)  # 路由路径
    component: str | None = Field(default=None, max_length=255)  # 组件路径
    is_active: int = Field(default=1)  # 是否启用
    method: str | None = Field(default=None, max_length=10)  # HTTP方法(GET/POST/PUT/DELETE)，用于PERMISSION类型
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    parent_id: str | None = Field(default=None, sa_column=Column(String(32), ForeignKey("sys_menus.id"), nullable=True))  # 父菜单ID
    meta_id: str = Field(sa_column=Column(String(32), ForeignKey("sys_menumeta.id"), nullable=False, unique=True))  # 菜单元数据ID(一对一)
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now()))
    description: str | None = Field(default=None, max_length=256)

    # 关系 - meta一对一关联
    meta: "MenuMeta" = Relationship(back_populates="menu", sa_relationship_kwargs={"lazy": "selectin", "uselist": False})  # noqa: F821

    def to_domain(self) -> "MenuEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.menu import MenuEntity

        return MenuEntity(
            id=self.id,
            menu_type=self.menu_type,
            name=self.name,
            rank=self.rank,
            path=self.path,
            component=self.component,
            is_active=self.is_active,
            method=self.method,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            parent_id=self.parent_id,
            meta_id=self.meta_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "MenuEntity") -> "Menu":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            menu_type=entity.menu_type,
            name=entity.name,
            rank=entity.rank,
            path=entity.path,
            component=entity.component,
            is_active=entity.is_active,
            method=entity.method,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            parent_id=entity.parent_id,
            meta_id=entity.meta_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<Menu(id={self.id}, name={self.name})>"
