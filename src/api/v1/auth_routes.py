"""V1 API - 认证路由。"""

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies import get_current_active_user
from src.application.dto.auth_dto import LoginDTO, RefreshTokenDTO, TokenResponseDTO
from src.application.services.auth_service import AuthService
from src.infrastructure.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponseDTO)
async def login(dto: LoginDTO, db: AsyncSession = Depends(get_db)) -> TokenResponseDTO:
    """认证用户并返回 JWT 令牌。"""
    service = AuthService(db)
    return await service.login(dto)


@router.post("/refresh", response_model=TokenResponseDTO)
async def refresh_token(dto: RefreshTokenDTO, db: AsyncSession = Depends(get_db)) -> TokenResponseDTO:
    """使用刷新令牌刷新访问令牌。"""
    service = AuthService(db)
    return await service.refresh_token(dto.refresh_token)


@router.get("/me")
async def get_current_user(current_user: dict = Depends(get_current_active_user)) -> dict:
    """获取当前认证用户信息。"""
    return current_user
