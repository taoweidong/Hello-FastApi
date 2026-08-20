"""角色-部门关联表模型。

用于自定义数据权限（data_scope=2）时记录角色可访问的部门范围。
"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlmodel import Field, SQLModel


class RoleDeptLink(SQLModel, table=True):
    """角色-部门关联表（自定义数据权限的部门范围）。"""

    __tablename__ = "sys_role_dept"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)  # 36位UUID
    role_id: str = Field(
        sa_column=Column(String(32), ForeignKey("sys_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    )
    dept_id: str = Field(
        sa_column=Column(String(32), ForeignKey("sys_departments.id", ondelete="CASCADE"), nullable=False, index=True)
    )

    def __repr__(self) -> str:
        return f"<RoleDeptLink(role_id={self.role_id}, dept_id={self.dept_id})>"
