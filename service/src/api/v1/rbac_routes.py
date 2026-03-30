"""System API - RBAC 管理路由模块。

提供角色和权限管理相关的接口，包括角色增删改查、权限分配等功能。
角色路由前缀: /api/system/role
权限路由前缀: /api/system/permission
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import list_response, page_response, success_response
from src.api.dependencies import require_permission
from src.application.dto.rbac_dto import (
    AssignPermissionsDTO,
    PermissionCreateDTO,
    PermissionListQueryDTO,
    RoleCreateDTO,
    RoleListQueryDTO,
    RoleUpdateDTO,
)
from src.application.services.rbac_service import RBACService
from src.infrastructure.database import get_db

# =============================================================================
# 角色管理路由
# =============================================================================

role_router = APIRouter()


@role_router.post("")
async def get_role_list(
    query: RoleListQueryDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role:view")),
):
    """获取角色列表接口（分页）。

    需要 role:view 权限。
    前端调用: POST /api/system/role
    响应格式: { list, total, pageSize, currentPage }

    Args:
        query: 角色列表查询参数（请求体）
        db: 数据库会话

    Returns:
        Pure Admin 标准分页响应格式的角色列表
    """
    service = RBACService(db)
    roles, total = await service.get_roles(query)

    # 转换为前端期望的字段格式
    role_list = []
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "status": role.status,
            "remark": role.remark or "",
            "createTime": int(role.createTime.timestamp() * 1000) if role.createTime else None,
        }
        role_list.append(role_dict)

    return list_response(
        list_data=role_list,
        total=total,
        page_size=query.pageSize,
        current_page=query.pageNum,
    )


@role_router.post("/create")
async def create_role(
    dto: RoleCreateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role:manage"))
):
    """创建角色接口。

    需要 role:manage 权限。
    前端调用: POST /api/system/role/create

    Args:
        dto: 角色创建数据
        db: 数据库会话

    Returns:
        统一响应格式的角色信息，code=201
    """
    service = RBACService(db)
    role = await service.create_role(dto)
    return success_response(data=role, message="角色创建成功", code=201)


@role_router.get("/{role_id}")
async def get_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role:view"))
):
    """获取角色详情接口。

    需要 role:view 权限。

    Args:
        role_id: 角色ID
        db: 数据库会话

    Returns:
        统一响应格式的角色详情（含权限列表）
    """
    service = RBACService(db)
    role = await service.get_role(role_id)
    return success_response(data=role)


@role_router.put("/{role_id}")
async def update_role(
    role_id: str,
    dto: RoleUpdateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role:manage")),
):
    """更新角色接口。

    需要 role:manage 权限。

    Args:
        role_id: 角色ID
        dto: 角色更新数据
        db: 数据库会话

    Returns:
        统一响应格式的更新后角色信息
    """
    service = RBACService(db)
    role = await service.update_role(role_id, dto)
    return success_response(data=role, message="角色更新成功")


@role_router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role:manage"))
):
    """删除角色接口。

    需要 role:manage 权限。

    Args:
        role_id: 角色ID
        db: 数据库会话

    Returns:
        统一响应格式的操作结果消息
    """
    service = RBACService(db)
    await service.delete_role(role_id)
    return success_response(message="角色删除成功")


@role_router.post("/{role_id}/permissions")
async def assign_permissions(
    role_id: str,
    dto: AssignPermissionsDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role:manage"))
):
    """为角色分配权限接口。

    需要 role:manage 权限。
    先清除角色的旧权限关联，再创建新的权限关联。

    Args:
        role_id: 角色ID
        dto: 权限分配数据（permissionIds列表）
        db: 数据库会话

    Returns:
        统一响应格式的操作结果消息
    """
    service = RBACService(db)
    await service.assign_permissions(role_id, dto.permissionIds)
    return success_response(message="权限分配成功")


@role_router.post("/{role_id}/menu")
async def assign_role_menu(
    role_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("role:manage"))
):
    """为角色分配菜单权限接口。

    需要 role:manage 权限。
    前端调用: POST /api/system/role/{id}/menu
    请求体: { menuIds: ["xxx", "yyy", "zzz"] }

    Args:
        role_id: 角色ID
        data: 菜单ID列表
        db: 数据库会话

    Returns:
        统一响应格式的操作结果消息
    """
    from src.infrastructure.repositories.rbac_repository import RoleRepository

    menu_ids = data.get("menuIds", [])
    role_repo = RoleRepository(db)

    # 为角色分配菜单权限
    await role_repo.assign_menus_to_role(role_id, menu_ids)
    await db.commit()

    return success_response(message="菜单权限分配成功")


# =============================================================================
# 权限管理路由
# =============================================================================

permission_router = APIRouter()


@permission_router.get("/list")
async def get_permission_list(
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
    permissionName: str = Query(None, description="权限名称"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("permission:view")),
):
    """获取权限列表接口（分页）。

    需要 permission:view 权限。

    Args:
        pageNum: 页码
        pageSize: 每页条数
        permissionName: 权限名称（模糊查询）
        db: 数据库会话

    Returns:
        分页响应格式的权限列表
    """
    # 构建查询DTO
    query = PermissionListQueryDTO(pageNum=pageNum, pageSize=pageSize, permissionName=permissionName)

    service = RBACService(db)
    permissions, total = await service.get_permissions(query)
    return page_response(rows=permissions, total=total, page_num=query.pageNum, page_size=query.pageSize)


@permission_router.post("/")
async def create_permission(
    dto: PermissionCreateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("permission:manage")),
):
    """创建权限接口。

    需要 permission:manage 权限。

    Args:
        dto: 权限创建数据
        db: 数据库会话

    Returns:
        统一响应格式的权限信息，code=201
    """
    service = RBACService(db)
    permission = await service.create_permission(dto)
    return success_response(data=permission, message="权限创建成功", code=201)


@permission_router.delete("/{permission_id}")
async def delete_permission(
    permission_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("permission:manage"))
):
    """删除权限接口。

    需要 permission:manage 权限。

    Args:
        permission_id: 权限ID
        db: 数据库会话

    Returns:
        统一响应格式的操作结果消息
    """
    service = RBACService(db)
    await service.delete_permission(permission_id)
    return success_response(message="权限删除成功")
