"""应用层 - 部门领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.core.validators import empty_str_or_zero_to_none, empty_str_to_none, normalize_optional_id


class DepartmentCreateDTO(BaseModel):
    """创建部门请求"""

    name: str = Field(max_length=64)
    parentId: str | None = Field(default=None, description="父部门ID，None表示顶级部门")
    sort: int = Field(default=0)
    principal: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=100)
    status: int = Field(default=1)
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v: str | None) -> str | None:
        """将 parentId 统一处理：空字符串、0、'0'、None 转换为 None。"""
        return normalize_optional_id(v)

    @field_validator("principal", "phone", "email", "remark", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator("sort", "status", mode="before")
    @classmethod
    def validate_empty_to_zero(cls, v: int | str | None) -> int:
        """将空字符串或 None 转换为 0。"""
        if v == "" or v is None:
            return 0
        return int(v) if isinstance(v, str) else v


class DepartmentUpdateDTO(BaseModel):
    """更新部门请求"""

    name: str | None = Field(default=None, max_length=64)
    parentId: str | None = Field(default=None, description="父部门ID")
    sort: int | None = None
    principal: str | None = Field(default=None, max_length=50)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=100)
    status: int | None = None
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v: str | None) -> str | None:
        """将 parentId 统一处理：空字符串、0、'0'、None 转换为 None。"""
        return normalize_optional_id(v)

    @field_validator("name", "principal", "phone", "email", "remark", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator("sort", "status", mode="before")
    @classmethod
    def validate_empty_or_zero(cls, v: int | str | None) -> int | None:
        """将空字符串或 0 转换为 None。"""
        return empty_str_or_zero_to_none(v)


class DepartmentResponseDTO(BaseModel):
    """部门响应"""

    id: str
    parentId: str | None
    name: str
    sort: int
    principal: str | None = None
    phone: str | None = None
    email: str | None = None
    status: int
    remark: str | None = None
    createTime: datetime | None = None

    model_config = {"from_attributes": True}


class DepartmentListQueryDTO(BaseModel):
    """部门列表查询请求"""

    name: str | None = None
    status: int | None = None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)
