"""安全领域 - IP 黑白名单和限流模型。"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class IPRule(Base):
    """IP 黑白名单规则实体。"""

    __tablename__ = "ip_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address: Mapped[str] = mapped_column(String(45), index=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(10), nullable=False)  # "whitelist" 或 "blacklist"
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<IPRule(ip={self.ip_address}, type={self.rule_type})>"
