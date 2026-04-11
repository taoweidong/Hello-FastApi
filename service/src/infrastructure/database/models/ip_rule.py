"""IP 黑白名单规则实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, func
from sqlmodel import Field, SQLModel


class IPRule(SQLModel, table=True):
    """IP 黑白名单规则实体。"""

    __tablename__ = "sys_ip_rules"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    ip_address: str = Field(max_length=45, index=True)
    rule_type: str = Field(max_length=10)  # "whitelist" 或 "blacklist"
    reason: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    expires_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    def __repr__(self) -> str:
        return f"<IPRule(ip={self.ip_address}, type={self.rule_type})>"
