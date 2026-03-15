"""应用层 - 认证服务。"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.auth_dto import LoginDTO, TokenResponseDTO
from src.core.exceptions import UnauthorizedError
from src.domain.auth.password_service import PasswordService
from src.domain.auth.token_service import TokenService
from src.infrastructure.repositories.user_repository import UserRepository


class AuthService:
    """认证操作的应用服务。"""

    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.token_service = TokenService()
        self.password_service = PasswordService()

    async def login(self, dto: LoginDTO) -> TokenResponseDTO:
        """认证用户并返回令牌。"""
        user = await self.user_repo.get_by_username(dto.username)
        if user is None:
            raise UnauthorizedError("Invalid username or password")

        if not self.password_service.verify_password(dto.password, user.hashed_password):
            raise UnauthorizedError("Invalid username or password")

        if not user.is_active:
            raise UnauthorizedError("User account is disabled")

        token_data = {"sub": user.id, "username": user.username}
        access_token = self.token_service.create_access_token(token_data)
        refresh_token = self.token_service.create_refresh_token(token_data)

        return TokenResponseDTO(access_token=access_token, refresh_token=refresh_token)

    async def refresh_token(self, refresh_token: str) -> TokenResponseDTO:
        """使用刷新令牌刷新访问令牌。"""
        payload = self.token_service.decode_token(refresh_token)
        if payload is None:
            raise UnauthorizedError("Invalid refresh token")

        if not self.token_service.verify_token_type(payload, "refresh"):
            raise UnauthorizedError("Invalid token type")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Invalid refresh token")

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or disabled")

        token_data = {"sub": user.id, "username": user.username}
        new_access_token = self.token_service.create_access_token(token_data)
        new_refresh_token = self.token_service.create_refresh_token(token_data)

        return TokenResponseDTO(access_token=new_access_token, refresh_token=new_refresh_token)
