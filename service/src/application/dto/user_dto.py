"""应用层 - 用户领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_or_zero_to_none, empty_str_to_none, normalize_optional_id


class UserProfileValidator:
    """用户档案字段验证器 Mixin"""

    @field_validator("nickname", "firstName", "lastName", "email", "phone", "avatar", "description", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        return empty_str_to_none(v)

    @field_validator("gender", "isStaff", "modeType", mode="before")
    @classmethod
    def validate_empty_or_zero(cls, v: int | str | None) -> int | None:
        return empty_str_or_zero_to_none(v)

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_is_active(cls, v: int | str | None) -> int | None:
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v


class UserCreateDTO(BaseModel, UserProfileValidator):
    """创建用户请求"""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    firstName: str | None = Field(default=None, max_length=64)
    lastName: str | None = Field(default=None, max_length=64)
    email: str | None = None
    phone: str | None = Field(default=None, max_length=20)
    gender: int | None = Field(default=None, description="性别(0-未知, 1-男, 2-女)")
    avatar: str | None = None
    isActive: int = Field(default=1, description="是否启用")
    isStaff: int = Field(default=0, description="是否为职员")
    modeType: int = Field(default=0, description="权限模式(0-OR, 1-AND)")
    dept_id: str | None = Field(default=None, alias="deptId")
    description: str | None = None

    model_config = {"populate_by_name": True}

    @field_validator("dept_id", mode="before")
    @classmethod
    def validate_dept_id(cls, v: str | int | None) -> str | None:
        return normalize_optional_id(v)


class UserUpdateDTO(BaseModel, UserProfileValidator):
    """更新用户请求"""

    nickname: str | None = Field(default=None, max_length=64)
    firstName: str | None = Field(default=None, max_length=64)
    lastName: str | None = Field(default=None, max_length=64)
    email: str | None = None
    phone: str | None = Field(default=None, max_length=20)
    gender: int | None = Field(default=None, description="性别(0-未知, 1-男, 2-女)")
    avatar: str | None = None
    isActive: int | None = Field(default=None, description="是否启用")
    isStaff: int | None = Field(default=None, description="是否为职员")
    modeType: int | None = Field(default=None, description="权限模式(0-OR, 1-AND)")
    dept_id: str | None = Field(default=None, alias="deptId")
    description: str | None = None

    model_config = {"populate_by_name": True}

    @field_validator("dept_id", mode="before")
    @classmethod
    def validate_dept_id(cls, v: str | int | None) -> str | None:
        return normalize_optional_id(v)


class UserResponseDTO(BaseModel):
    """用户响应"""

    id: str
    username: str
    nickname: str | None = None
    firstName: str | None = None
    lastName: str | None = None
    avatar: str | None = None
    email: str | None = None
    phone: str | None = None
    gender: int | None = None
    isActive: int = 1
    isStaff: int = 0
    modeType: int = 0
    roles: list[dict] = []
    creatorId: str | None = None
    modifierId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class UserListQueryDTO(BaseModel):
    """用户列表查询请求"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    username: str | None = None
    phone: str | None = None
    email: str | None = None
    isActive: int | None = None
    deptId: str | None = None

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_empty(cls, v):
        return empty_str_to_none(v)

    @field_validator("deptId", mode="before")
    @classmethod
    def validate_dept_id(cls, v: str | int | None) -> str | None:
        return normalize_optional_id(v)


class ChangePasswordDTO(BaseModel):
    """修改密码请求"""

    oldPassword: str
    newPassword: str = Field(min_length=8, max_length=128)


class ResetPasswordDTO(BaseModel):
    """重置密码请求"""

    newPassword: str = Field(min_length=8, max_length=128)


class UpdateStatusDTO(BaseModel):
    """更改用户状态请求"""

    isActive: int = Field(ge=0, le=1)


class BatchDeleteDTO(BaseModel):
    """批量删除请求"""

    ids: list[str]


class AssignRoleDTO(BaseModel):
    """分配角色请求"""

    userId: str
    roleIds: list[str]
