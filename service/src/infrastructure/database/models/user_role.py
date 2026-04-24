"""用户-角色关联表模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from typing import Optional

from sqlalchemy import Column, ForeignKey, String
from sqlmodel import Field, Relationship, SQLModel


class UserRole(SQLModel, table=True):
    """用户-角色关联表。"""

    __tablename__ = "sys_userinfo_roles"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    userinfo_id: str = Field(
        sa_column=Column(String(32), ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False)
    )
    userrole_id: str = Field(
        sa_column=Column(String(32), ForeignKey("sys_roles.id", ondelete="CASCADE"), nullable=False)
    )

    # 关系 - 使用字符串引用避免循环导入
    user: Optional["User"] = Relationship(back_populates="roles")  # noqa: F821
    role: Optional["Role"] = Relationship(back_populates="users")  # noqa: F821

    def __repr__(self) -> str:
        return f"<UserRole(userinfo_id={self.userinfo_id}, userrole_id={self.userrole_id})>"
