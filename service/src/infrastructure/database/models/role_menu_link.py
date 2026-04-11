"""角色-菜单关联表模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

from sqlalchemy import Column, ForeignKey, String
from sqlmodel import Field, SQLModel


class RoleMenuLink(SQLModel, table=True):
    """角色-菜单关联表（用于多对多关系）。"""

    __tablename__ = "sys_role_menus"

    role_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True))
    menu_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_menus.id", ondelete="CASCADE"), primary_key=True))
