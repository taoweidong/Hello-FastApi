"""IP 规则领域实体。

定义 IP 黑白名单规则的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


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
