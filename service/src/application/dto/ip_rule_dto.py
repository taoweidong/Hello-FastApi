"""应用层 - IP 规则领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_to_none


class IPRuleListQueryDTO(BaseModel):
    """IP 规则列表查询"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    ruleType: str | None = None
    isActive: int | None = None
    createdTime: str | list[str] | None = None

    @field_validator("ruleType", "isActive", "createdTime", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)


class IPRuleCreateDTO(BaseModel):
    """创建 IP 规则"""

    ipAddress: str = Field(min_length=1, max_length=64)
    ruleType: str = Field(default="blacklist", min_length=1, max_length=32)
    reason: str | None = Field(default=None, max_length=256)
    isActive: int = Field(default=1, ge=0, le=1)
    expiresAt: datetime | None = None

    @field_validator("reason", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)


class IPRuleUpdateDTO(BaseModel):
    """更新 IP 规则"""

    ipAddress: str | None = Field(default=None, min_length=1, max_length=64)
    ruleType: str | None = Field(default=None, min_length=1, max_length=32)
    reason: str | None = Field(default=None, max_length=256)
    isActive: int | None = Field(default=None, ge=0, le=1)
    expiresAt: datetime | None = None
    description: str | None = Field(default=None, max_length=256)

    @field_validator("reason", "description", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)

    @field_validator("ipAddress", "ruleType", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v):
        return empty_str_to_none(v)


class IPRuleResponseDTO(BaseModel):
    """IP 规则响应"""

    id: str
    ipAddress: str
    ruleType: str
    reason: str = ""
    isActive: int
    creatorId: str | None = None
    modifierId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None
    expiresAt: datetime | None = None
    description: str = ""


class IPRuleBatchDeleteDTO(BaseModel):
    """批量删除 IP 规则请求"""

    ids: list[str] = Field(default_factory=list)
