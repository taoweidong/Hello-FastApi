"""岗位实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.post import PostEntity


class Post(SQLModel, table=True):
    """岗位实体。"""

    __tablename__ = "sys_post"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)  # 36 位 UUID 主键
    post_code: str = Field(max_length=64, index=True)  # 岗位编码（唯一）
    post_name: str = Field(max_length=64)  # 岗位名称
    post_sort: int = Field(default=0)  # 显示排序
    is_active: int = Field(default=1)  # 状态（1正常 0停用）
    remark: str = Field(default="", max_length=256)  # 备注
    creator_id: str | None = Field(default=None, max_length=32)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=32)  # 修改人ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now())
    )

    def to_domain(self) -> "PostEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.post import PostEntity

        return PostEntity(
            id=self.id,
            post_code=self.post_code,
            post_name=self.post_name,
            post_sort=self.post_sort,
            is_active=self.is_active,
            remark=self.remark,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
        )

    @classmethod
    def from_domain(cls, entity: "PostEntity") -> "Post":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            post_code=entity.post_code,
            post_name=entity.post_name,
            post_sort=entity.post_sort,
            is_active=entity.is_active,
            remark=entity.remark,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
        )

    def __repr__(self) -> str:
        return f"<Post(id={self.id}, post_code={self.post_code})>"
