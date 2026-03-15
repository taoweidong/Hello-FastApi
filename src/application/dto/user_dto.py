"""应用层 - 用户领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreateDTO(BaseModel):
    """创建新用户 DTO。"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=100)


class UserUpdateDTO(BaseModel):
    """更新用户 DTO。"""

    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class UserResponseDTO(BaseModel):
    """用户响应 DTO。"""

    id: str
    username: str
    email: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    roles: list[str] = []

    model_config = {"from_attributes": True}


class UserListResponseDTO(BaseModel):
    """分页用户列表响应 DTO。"""

    total: int
    items: list[UserResponseDTO]


class ChangePasswordDTO(BaseModel):
    """修改密码 DTO。"""

    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
