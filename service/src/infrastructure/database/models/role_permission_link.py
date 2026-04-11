"""角色-权限关联表（用于多对多关系）。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

from sqlalchemy import Column, ForeignKey, String
from sqlmodel import Field, SQLModel


class RolePermissionLink(SQLModel, table=True):
    """角色-权限关联表（用于多对多关系）。"""

    __tablename__ = "sys_role_permissions"

    role_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True))
    permission_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_permissions.id", ondelete="CASCADE"), primary_key=True))
