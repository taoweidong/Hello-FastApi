"""系统配置实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.system_config import SystemConfigEntity


class SystemConfig(SQLModel, table=True):
    """系统配置实体（键值配置）。"""

    __tablename__ = "sys_systemconfig"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    value: str = Field(sa_column=Column(Text, nullable=False))  # 配置值(JSON格式)
    is_active: int = Field(default=1)  # 是否启用
    access: int = Field(default=0)  # 访问级别
    key: str = Field(max_length=255, unique=True)  # 配置键(唯一)
    inherit: int = Field(default=0)  # 是否继承
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now()))
    description: str | None = Field(default=None, max_length=256)

    def to_domain(self) -> "SystemConfigEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.system_config import SystemConfigEntity

        return SystemConfigEntity(
            id=self.id,
            value=self.value,
            is_active=self.is_active,
            access=self.access,
            key=self.key,
            inherit=self.inherit,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "SystemConfigEntity") -> "SystemConfig":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            value=entity.value,
            is_active=entity.is_active,
            access=entity.access,
            key=entity.key,
            inherit=entity.inherit,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<SystemConfig(id={self.id}, key={self.key})>"
