"""应用层 - 角色领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_to_none


class RoleCreateDTO(BaseModel):
    """创建角色请求"""

    name: str = Field(min_length=2, max_length=64)
    code: str = Field(min_length=2, max_length=64)
    isActive: int = Field(default=1, description="是否启用")
    # 数据权限范围：1全部/2自定义/3本部门/4本部门及以下/5仅本人
    dataScope: int = Field(default=1, ge=1, le=5, description="数据权限范围")
    description: str | None = Field(default=None, max_length=500)
    menuIds: list[str] = []
    deptIds: list[str] = Field(default=[], description="自定义数据权限的部门ID列表（dataScope=2 时生效）")

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
    dataScope: int | None = Field(default=None, ge=1, le=5, description="数据权限范围")
    description: str | None = Field(default=None, max_length=500)
    menuIds: list[str] | None = None
    deptIds: list[str] | None = Field(default=None, description="自定义数据权限的部门ID列表")

    @field_validator("name", "code", "description", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_status(cls, v: int | str | None) -> int | None:
        """将空字符串转换为 None，保留 0 值。"""
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v


class RoleResponseDTO(BaseModel):
    """角色响应"""

    id: str
    name: str
    code: str
    isActive: int = 1
    dataScope: int = 1
    menus: list[dict] = []
    deptIds: list[str] = []
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


class RoleStatusUpdateDTO(BaseModel):
    """角色状态更新请求"""

    isActive: int = Field(ge=0, le=1)
