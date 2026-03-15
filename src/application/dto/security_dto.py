"""应用层 - 安全领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field


class IPRuleCreateDTO(BaseModel):
    """创建 IP 规则 DTO。"""

    ip_address: str
    rule_type: str = Field(..., pattern="^(whitelist|blacklist)$")
    reason: str | None = None
    expires_at: datetime | None = None


class IPRuleResponseDTO(BaseModel):
    """IP 规则响应 DTO。"""

    id: str
    ip_address: str
    rule_type: str
    reason: str | None = None
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None

    model_config = {"from_attributes": True}
