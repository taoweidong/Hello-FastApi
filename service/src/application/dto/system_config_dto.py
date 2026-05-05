"""应用层 - 系统配置领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_or_zero_to_none, empty_str_to_none


class SystemConfigCreateDTO(BaseModel):
    """创建系统配置请求"""

    key: str = Field(min_length=1, max_length=255, description="配置键(唯一)")
    value: str = Field(description="配置值(JSON格式)")
    isActive: int = Field(default=1, description="是否启用")
    access: int = Field(default=0, description="访问级别")
    inherit: int = Field(default=0, description="是否继承")
    description: str | None = Field(default=None, max_length=256)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class SystemConfigUpdateDTO(BaseModel):
    """更新系统配置请求"""

    key: str | None = Field(default=None, min_length=1, max_length=255, description="配置键(唯一)")
    value: str | None = Field(default=None, description="配置值(JSON格式)")
    isActive: int | None = Field(default=None, description="是否启用")
    access: int | None = Field(default=None, description="访问级别")
    inherit: int | None = Field(default=None, description="是否继承")
    description: str | None = Field(default=None, max_length=256)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator("isActive", "access", "inherit", mode="before")
    @classmethod
    def validate_empty_or_zero(cls, v: int | str | None) -> int | None:
        """将空字符串或 0 转换为 None。"""
        return empty_str_or_zero_to_none(v)


class SystemConfigResponseDTO(BaseModel):
    """系统配置响应"""

    id: str
    key: str
    value: str
    isActive: int = 1
    access: int = 0
    inherit: int = 0
    creatorId: str | None = None
    modifierId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class SystemConfigListQueryDTO(BaseModel):
    """系统配置列表查询"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    key: str | None = None
    isActive: int | None = None

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_status(cls, v):
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)
