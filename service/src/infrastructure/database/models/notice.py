"""通知公告实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.notice import NoticeEntity


class Notice(SQLModel, table=True):
    """通知公告实体。"""

    __tablename__ = "sys_notice"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)  # 36 位 UUID 主键
    title: str = Field(max_length=128)  # 公告标题
    content: str = Field(default="")  # 公告内容
    notice_type: int = Field(default=1)  # 公告类型（1通知 2公告）
    is_active: int = Field(default=1)  # 状态（1正常 0关闭）
    publisher_id: str | None = Field(default=None, max_length=32)  # 发布人ID
    publisher_name: str = Field(default="", max_length=64)  # 发布人名称（冗余，避免联查）
    creator_id: str | None = Field(default=None, max_length=32)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=32)  # 修改人ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now())
    )

    def to_domain(self) -> "NoticeEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.notice import NoticeEntity

        return NoticeEntity(
            id=self.id,
            title=self.title,
            content=self.content,
            notice_type=self.notice_type,
            is_active=self.is_active,
            publisher_id=self.publisher_id,
            publisher_name=self.publisher_name,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
        )

    @classmethod
    def from_domain(cls, entity: "NoticeEntity") -> "Notice":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            title=entity.title,
            content=entity.content,
            notice_type=entity.notice_type,
            is_active=entity.is_active,
            publisher_id=entity.publisher_id,
            publisher_name=entity.publisher_name,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
        )

    def __repr__(self) -> str:
        return f"<Notice(id={self.id}, title={self.title})>"
