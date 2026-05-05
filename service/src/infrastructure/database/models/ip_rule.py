"""IP 黑白名单规则实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.ip_rule import IPRuleEntity


class IPRule(SQLModel, table=True):
    """IP 黑白名单规则实体。"""

    __tablename__ = "sys_ip_rules"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    ip_address: str = Field(max_length=45, index=True)
    rule_type: str = Field(max_length=10)  # "whitelist" 或 "blacklist"
    reason: str | None = Field(default=None, max_length=255)
    is_active: int = Field(default=1)  # 是否启用
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now())
    )
    expires_at: datetime | None = Field(default=None, sa_column=Column(DateTime, nullable=True))
    description: str | None = Field(default=None, max_length=256)

    def to_domain(self) -> "IPRuleEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.ip_rule import IPRuleEntity

        return IPRuleEntity(
            id=self.id,
            ip_address=self.ip_address,
            rule_type=self.rule_type,
            reason=self.reason,
            is_active=self.is_active,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
            expires_at=self.expires_at,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "IPRuleEntity") -> "IPRule":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            ip_address=entity.ip_address,
            rule_type=entity.rule_type,
            reason=entity.reason,
            is_active=entity.is_active,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            expires_at=entity.expires_at,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<IPRule(ip={self.ip_address}, type={self.rule_type})>"
