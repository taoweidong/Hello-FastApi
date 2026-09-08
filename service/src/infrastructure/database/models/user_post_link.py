"""用户-岗位关联表模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlmodel import Field, SQLModel


class UserPostLink(SQLModel, table=True):
    """用户-岗位关联表。"""

    __tablename__ = "sys_user_post"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(sa_column=Column(String(32), ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False))
    post_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_post.id", ondelete="CASCADE"), nullable=False))

    def __repr__(self) -> str:
        return f"<UserPostLink(user_id={self.user_id}, post_id={self.post_id})>"
