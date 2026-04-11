"""用户-角色关联表模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlmodel import Field, Relationship, SQLModel


class UserRole(SQLModel, table=True):
    """用户-角色关联表。"""

    __tablename__ = "sys_user_roles"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False))
    role_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_roles.id", ondelete="CASCADE"), nullable=False))
    assigned_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    # 关系 - 使用字符串引用避免循环导入
    user: Optional["User"] = Relationship(back_populates="roles")  # noqa: F821
    role: Optional["Role"] = Relationship(back_populates="users")  # noqa: F821

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
