"""应用层 - 认证领域的数据传输对象。"""

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.application.validators import empty_str_to_none, normalize_optional_id


class LoginDTO(BaseModel):
    """登录请求"""

    username: str
    password: str


class RegisterDTO(BaseModel):
    """注册请求。

    匿名可打点面，校验与管理端 UserCreateDTO 对齐（用户名≥3 位、密码≥8 位），
    防止 1 位用户名+1 位密码的弱账号直接注册入库。
    """

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    nickname: str | None = Field(default=None, max_length=64)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)


class RefreshTokenDTO(BaseModel):
    """刷新令牌请求"""

    refreshToken: str


class LogoutDTO(BaseModel):
    """登出请求。

    refreshToken 可选：前端登出时携带，后端将 access_token（Header）与
    refresh_token（Body）一并写入黑名单，防止登出后仍可用 refresh_token 换发新令牌。
    """

    refreshToken: str | None = None


class UserInfoDTO(BaseModel):
    """用户信息（嵌入登录响应中）"""

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

    model_config = {"from_attributes": True}


class TokenResponseDTO(BaseModel):
    """登录/刷新响应"""

    accessToken: str
    expires: int  # 过期时间（秒）
    refreshToken: str


class LoginResponseDTO(BaseModel):
    """完整登录响应（含用户信息）"""

    accessToken: str
    expires: int
    refreshToken: str
    userInfo: UserInfoDTO | None = None
    roles: list[str] = []


class UserIdRequestDTO(BaseModel):
    """按用户 ID 查询角色列表请求"""

    userId: str | int = Field(min_length=1)

    @field_validator("userId", mode="before")
    @classmethod
    def _normalize(cls, v):
        return normalize_optional_id(empty_str_to_none(v))


class RoleIdRequestDTO(BaseModel):
    """按角色 ID 查询菜单列表请求"""

    id: str | int = Field(min_length=1)

    @field_validator("id", mode="before")
    @classmethod
    def _normalize(cls, v):
        return normalize_optional_id(empty_str_to_none(v))


class MineUserDTO(BaseModel):
    """当前登录用户简要信息响应"""

    avatar: str = ""
    username: str
    nickname: str
    email: str = ""
    phone: str = ""
    description: str = ""


class RoleMenuItemDTO(BaseModel):
    """角色菜单权限项响应"""

    parentId: int | str
    id: int | str
    menuType: int
    title: str
