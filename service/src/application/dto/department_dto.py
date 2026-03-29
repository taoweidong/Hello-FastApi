"""应用层 - 部门领域的数据传输对象。"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


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

    @field_validator('parentId', 'principal', 'phone', 'email', 'remark', mode='before')
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        """将空字符串转换为None"""
        if v == '' or v == '0' or v == 0:
            return None
        return v

    @field_validator('sort', 'status', mode='before')
    @classmethod
    def empty_str_to_zero(cls, v: int | str | None) -> int:
        """将空字符串或None转换为0"""
        if v == '' or v is None:
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

    @field_validator('parentId', 'name', 'principal', 'phone', 'email', 'remark', mode='before')
    @classmethod
    def empty_str_to_none(cls, v: str | None) -> str | None:
        """将空字符串转换为None"""
        if v == '' or v == '0' or v == 0:
            return None
        return v

    @field_validator('sort', 'status', mode='before')
    @classmethod
    def empty_str_or_zero_to_none(cls, v: int | str | None) -> int | None:
        """将空字符串或0转换为None"""
        if v == '' or v == 0 or v is None:
            return None
        return int(v) if isinstance(v, str) else v


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

    @field_validator('status', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """将空字符串转换为None"""
        if v == '' or v is None:
            return None
        return int(v) if isinstance(v, str) else v
