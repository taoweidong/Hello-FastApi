"""IP 规则领域实体。

定义 IP 黑白名单规则的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class IPRuleEntity:
    """IP 黑白名单规则领域实体。

    Attributes:
        id: 规则唯一标识（32位UUID字符串）
        ip_address: IP地址
        rule_type: 规则类型(whitelist/blacklist)
        reason: 规则原因说明
        is_active: 是否启用
        creator_id: 创建人ID
        modifier_id: 修改人ID
        created_time: 创建时间
        updated_time: 更新时间
        expires_at: 过期时间
        description: 描述
    """

    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"

    id: str
    ip_address: str = ""
    rule_type: str = "blacklist"
    reason: str | None = None
    is_active: int = 1
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    expires_at: datetime | None = None
    description: str | None = None

    # ---- 状态查询属性 ----

    @property
    def is_whitelist(self) -> bool:
        """是否为白名单规则。"""
        return self.rule_type == self.WHITELIST

    @property
    def is_blacklist(self) -> bool:
        """是否为黑名单规则。"""
        return self.rule_type == self.BLACKLIST

    @property
    def is_expired(self) -> bool:
        """规则是否已过期。"""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_effective(self) -> bool:
        """规则是否生效（启用且未过期）。"""
        return self.is_active == 1 and not self.is_expired

    # ---- 状态变更方法 ----

    def update_info(self, *, ip_address: str | None = None, rule_type: str | None = None, reason: str | None = None, is_active: int | None = None, expires_at: datetime | None = None, description: str | None = None) -> None:
        """有条件地更新IP规则信息。"""
        if ip_address is not None:
            self.ip_address = ip_address
        if rule_type is not None:
            self.rule_type = rule_type
        if reason is not None:
            self.reason = reason
        if is_active is not None:
            self.is_active = is_active
        if expires_at is not None:
            self.expires_at = expires_at
        if description is not None:
            self.description = description

    # ---- 工厂方法 ----

    @classmethod
    def create_new(cls, ip_address: str, rule_type: str = "blacklist", reason: str | None = None, is_active: int = 1, expires_at: datetime | None = None, description: str | None = None) -> IPRuleEntity:
        """创建新IP规则实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            ip_address=ip_address,
            rule_type=rule_type,
            reason=reason,
            is_active=is_active,
            expires_at=expires_at,
            description=description,
        )
