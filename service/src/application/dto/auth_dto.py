"""应用层 - 认证领域的数据传输对象。"""

from pydantic import BaseModel


class LoginDTO(BaseModel):
    """登录请求"""

    username: str
    password: str


class RegisterDTO(BaseModel):
    """注册请求"""

    username: str
    password: str
    nickname: str | None = None
    email: str | None = None
    phone: str | None = None


class RefreshTokenDTO(BaseModel):
    """刷新令牌请求"""

    refreshToken: str


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
