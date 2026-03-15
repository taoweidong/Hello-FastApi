"""应用层 - 认证领域的数据传输对象。"""

from sqlmodel import SQLModel


class LoginDTO(SQLModel):
    """用户登录 DTO。"""

    username: str
    password: str


class TokenResponseDTO(SQLModel):
    """令牌响应 DTO。"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenDTO(SQLModel):
    """令牌刷新请求 DTO。"""

    refresh_token: str
