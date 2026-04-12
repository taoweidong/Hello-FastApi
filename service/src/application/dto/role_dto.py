"""应用层 - 角色领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_or_zero_to_none, empty_str_to_none


class RoleCreateDTO(BaseModel):
    """创建角色请求"""

    name: str = Field(min_length=2, max_length=64)
    code: str = Field(min_length=2, max_length=64)
    isActive: int = Field(default=1, description="是否启用")
    description: str | None = Field(default=None, max_length=500)
    menuIds: list[str] = []

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class RoleUpdateDTO(BaseModel):
    """更新角色请求"""

    name: str | None = Field(default=None, min_length=2, max_length=64)
    code: str | None = Field(default=None, min_length=2, max_length=64)
    isActive: int | None = Field(default=None, description="是否启用")
    description: str | None = Field(default=None, max_length=500)
    menuIds: list[str] | None = None

    @field_validator("name", "code", "description", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_status(cls, v: int | str | None) -> int | None:
        """将空字符串或 0 转换为 None。"""
        return empty_str_or_zero_to_none(v)


class RoleResponseDTO(BaseModel):
    """角色响应"""

    id: str
    name: str
    code: str
    isActive: int = 1
    menus: list[dict] = []
    creatorId: str | None = None
    modifierId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class RoleListQueryDTO(BaseModel):
    """角色列表查询"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    name: str | None = None
    code: str | None = None
    isActive: int | None = None

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_status(cls, v):
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class AssignMenusDTO(BaseModel):
    """分配菜单请求"""

    menuIds: list[str]


class AssignRoleDTO(BaseModel):
    """分配角色请求"""

    userId: str = Field(alias="userId")
    roleId: str = Field(alias="roleId")

    model_config = {"populate_by_name": True}
