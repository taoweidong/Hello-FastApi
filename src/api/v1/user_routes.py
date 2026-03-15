"""V1 API - 用户管理路由。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import MessageResponse
from src.api.dependencies import (
    get_current_user_id,
    require_permission,
)
from src.application.dto.user_dto import (
    ChangePasswordDTO,
    UserCreateDTO,
    UserListResponseDTO,
    UserResponseDTO,
    UserUpdateDTO,
)
from src.application.services.user_service import UserService
from src.infrastructure.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponseDTO, status_code=201)
async def create_user(
    dto: UserCreateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user.create")),
) -> UserResponseDTO:
    """创建新用户（需要 user.create 权限）。"""
    service = UserService(db)
    return await service.create_user(dto)


@router.get("", response_model=UserListResponseDTO)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user.view")),
) -> UserListResponseDTO:
    """获取所有用户列表（分页）（需要 user.view 权限）。"""
    service = UserService(db)
    users = await service.get_users(skip=skip, limit=limit)
    total = await service.get_users_count()
    return UserListResponseDTO(total=total, items=users)


@router.get("/me", response_model=UserResponseDTO)
async def get_my_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserResponseDTO:
    """获取当前用户资料。"""
    service = UserService(db)
    return await service.get_user(user_id)


@router.put("/me", response_model=UserResponseDTO)
async def update_my_profile(
    dto: UserUpdateDTO,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserResponseDTO:
    """更新当前用户资料。"""
    service = UserService(db)
    return await service.update_user(user_id, dto)


@router.post("/me/change-password", response_model=MessageResponse)
async def change_my_password(
    dto: ChangePasswordDTO,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """修改当前用户密码。"""
    service = UserService(db)
    await service.change_password(user_id, dto)
    return MessageResponse(message="Password changed successfully")


@router.get("/{user_id}", response_model=UserResponseDTO)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user.view")),
) -> UserResponseDTO:
    """根据 ID 获取用户（需要 user.view 权限）。"""
    service = UserService(db)
    return await service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponseDTO)
async def update_user(
    user_id: str,
    dto: UserUpdateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user.update")),
) -> UserResponseDTO:
    """根据 ID 更新用户（需要 user.update 权限）。"""
    service = UserService(db)
    return await service.update_user(user_id, dto)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user.delete")),
) -> MessageResponse:
    """根据 ID 删除用户（需要 user.delete 权限）。"""
    service = UserService(db)
    await service.delete_user(user_id)
    return MessageResponse(message="User deleted successfully")
