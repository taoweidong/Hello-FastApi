"""角色-菜单关联表模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlmodel import Field, SQLModel


class RoleMenuLink(SQLModel, table=True):
    """角色-菜单关联表（用于多对多关系）。"""

    __tablename__ = "sys_userrole_menu"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    userrole_id: str = Field(sa_column=Column(String(32), ForeignKey("sys_roles.id", ondelete="CASCADE"), nullable=False))
    menu_id: str = Field(sa_column=Column(String(32), ForeignKey("sys_menus.id", ondelete="CASCADE"), nullable=False))

    def __repr__(self) -> str:
        return f"<RoleMenuLink(userrole_id={self.userrole_id}, menu_id={self.menu_id})>"
