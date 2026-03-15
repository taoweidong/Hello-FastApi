"""V1 API - RBAC 管理路由。"""

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import MessageResponse
from src.api.dependencies import require_permission
from src.application.dto.rbac_dto import (
    AssignRoleDTO,
    PermissionCreateDTO,
    PermissionResponseDTO,
    RoleCreateDTO,
    RoleResponseDTO,
    RoleUpdateDTO,
)
from src.application.services.rbac_service import RBACService
from src.infrastructure.database import get_db

router = APIRouter(prefix="/rbac", tags=["RBAC"])


# --- 角色端点 ---


@router.post("/roles", response_model=RoleResponseDTO, status_code=201)
async def create_role(
    dto: RoleCreateDTO, db: AsyncSession = Depends(get_db), _: dict = Depends(require_permission("role.manage"))
) -> RoleResponseDTO:
    """创建新角色（需要 role.manage 权限）。"""
    service = RBACService(db)
    return await service.create_role(dto)


@router.get("/roles", response_model=list[RoleResponseDTO])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role.view")),
) -> list[RoleResponseDTO]:
    """获取所有角色列表（需要 role.view 权限）。"""
    service = RBACService(db)
    return await service.get_roles(skip=skip, limit=limit)


@router.get("/roles/{role_id}", response_model=RoleResponseDTO)
async def get_role(
    role_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(require_permission("role.view"))
) -> RoleResponseDTO:
    """根据 ID 获取角色（需要 role.view 权限）。"""
    service = RBACService(db)
    return await service.get_role(role_id)


@router.put("/roles/{role_id}", response_model=RoleResponseDTO)
async def update_role(
    role_id: str,
    dto: RoleUpdateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role.manage")),
) -> RoleResponseDTO:
    """更新角色（需要 role.manage 权限）。"""
    service = RBACService(db)
    return await service.update_role(role_id, dto)


@router.delete("/roles/{role_id}", response_model=MessageResponse)
async def delete_role(
    role_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(require_permission("role.manage"))
) -> MessageResponse:
    """删除角色（需要 role.manage 权限）。"""
    service = RBACService(db)
    await service.delete_role(role_id)
    return MessageResponse(message="Role deleted successfully")


# --- 权限端点 ---


@router.post("/permissions", response_model=PermissionResponseDTO, status_code=201)
async def create_permission(
    dto: PermissionCreateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("permission.manage")),
) -> PermissionResponseDTO:
    """创建新权限（需要 permission.manage 权限）。"""
    service = RBACService(db)
    return await service.create_permission(dto)


@router.get("/permissions", response_model=list[PermissionResponseDTO])
async def list_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("permission.view")),
) -> list[PermissionResponseDTO]:
    """获取所有权限列表（需要 permission.view 权限）。"""
    service = RBACService(db)
    return await service.get_permissions(skip=skip, limit=limit)


@router.delete("/permissions/{permission_id}", response_model=MessageResponse)
async def delete_permission(
    permission_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(require_permission("permission.manage"))
) -> MessageResponse:
    """删除权限（需要 permission.manage 权限）。"""
    service = RBACService(db)
    await service.delete_permission(permission_id)
    return MessageResponse(message="Permission deleted successfully")


# --- 分配端点 ---


@router.post("/assign-role", response_model=MessageResponse)
async def assign_role_to_user(
    dto: AssignRoleDTO, db: AsyncSession = Depends(get_db), _: dict = Depends(require_permission("role.manage"))
) -> MessageResponse:
    """为用户分配角色（需要 role.manage 权限）。"""
    service = RBACService(db)
    await service.assign_role_to_user(dto.user_id, dto.role_id)
    return MessageResponse(message="Role assigned successfully")


@router.post("/remove-role", response_model=MessageResponse)
async def remove_role_from_user(
    dto: AssignRoleDTO, db: AsyncSession = Depends(get_db), _: dict = Depends(require_permission("role.manage"))
) -> MessageResponse:
    """移除用户的角色（需要 role.manage 权限）。"""
    service = RBACService(db)
    await service.remove_role_from_user(dto.user_id, dto.role_id)
    return MessageResponse(message="Role removed successfully")


@router.get("/users/{user_id}/roles", response_model=list[RoleResponseDTO])
async def get_user_roles(
    user_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(require_permission("role.view"))
) -> list[RoleResponseDTO]:
    """获取用户的所有角色（需要 role.view 权限）。"""
    service = RBACService(db)
    return await service.get_user_roles(user_id)


@router.get("/users/{user_id}/permissions", response_model=list[PermissionResponseDTO])
async def get_user_permissions(
    user_id: str, db: AsyncSession = Depends(get_db), _: dict = Depends(require_permission("permission.view"))
) -> list[PermissionResponseDTO]:
    """获取用户的所有权限（需要 permission.view 权限）。"""
    service = RBACService(db)
    return await service.get_user_permissions(user_id)
