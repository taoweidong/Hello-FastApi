"""应用层 - 用户领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.core.validators import empty_str_or_zero_to_none, empty_str_to_none


class UserCreateDTO(BaseModel):
    """创建用户请求"""
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    email: str | None = None
    phone: str | None = Field(default=None, max_length=20)
    sex: int | None = None
    avatar: str | None = None
    status: int = 1
    dept_id: int | None = Field(default=None, alias="deptId")
    remark: str | None = None

    model_config = {"populate_by_name": True}

    @field_validator('nickname', 'email', 'phone', 'avatar', 'remark', mode='before')
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator('sex', 'status', 'dept_id', mode='before')
    @classmethod
    def validate_empty_or_zero(cls, v: int | str | None) -> int | None:
        """将空字符串或 0 转换为 None。"""
        return empty_str_or_zero_to_none(v)


class UserUpdateDTO(BaseModel):
    """更新用户请求"""
    nickname: str | None = Field(default=None, max_length=64)
    email: str | None = None
    phone: str | None = Field(default=None, max_length=20)
    sex: int | None = None
    avatar: str | None = None
    status: int | None = None
    dept_id: int | None = Field(default=None, alias="deptId")
    remark: str | None = None

    model_config = {"populate_by_name": True}

    @field_validator('nickname', 'email', 'phone', 'avatar', 'remark', mode='before')
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator('sex', 'status', 'dept_id', mode='before')
    @classmethod
    def validate_empty_or_zero(cls, v: int | str | None) -> int | None:
        """将空字符串或 0 转换为 None。"""
        return empty_str_or_zero_to_none(v)


class UserResponseDTO(BaseModel):
    """用户响应"""
    id: str
    username: str
    nickname: str | None = None
    avatar: str | None = None
    email: str | None = None
    phone: str | None = None
    sex: int | None = None
    status: int = 1
    roles: list[dict] = []
    permissions: list[str] = []
    createTime: datetime | None = None
    updateTime: datetime | None = None

    model_config = {"from_attributes": True}


class UserListQueryDTO(BaseModel):
    """用户列表查询请求"""
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    username: str | None = None
    phone: str | None = None
    email: str | None = None
    status: int | None = None
    deptId: int | None = None

    @field_validator('status', 'deptId', mode='before')
    @classmethod
    def validate_empty(cls, v):
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class ChangePasswordDTO(BaseModel):
    """修改密码请求"""
    oldPassword: str
    newPassword: str = Field(min_length=8, max_length=128)


class ResetPasswordDTO(BaseModel):
    """重置密码请求"""
    newPassword: str = Field(min_length=8, max_length=128)


class UpdateStatusDTO(BaseModel):
    """更改用户状态请求"""
    status: int = Field(ge=0, le=1)


class BatchDeleteDTO(BaseModel):
    """批量删除请求"""
    ids: list[str]


class AssignRoleDTO(BaseModel):
    """分配角色请求"""
    userId: str
    roleIds: list[str]
