"""System API - 角色管理路由模块。

提供角色管理相关的接口，包括角色增删改查、权限分配等功能。
路由前缀: /api/system/role
"""

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import datetime_to_timestamp, list_response, success_response
from src.api.dependencies import get_role_repository, get_role_service, require_permission
from src.application.dto.role_dto import AssignPermissionsDTO, RoleCreateDTO, RoleListQueryDTO, RoleUpdateDTO
from src.application.services.role_service import RoleService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.role_repository import RoleRepository

role_router = APIRouter()


@role_router.post("")
async def get_role_list(query: RoleListQueryDTO, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:view"))):
    """获取角色列表接口（分页）。

    需要 role:view 权限。
    前端调用: POST /api/system/role
    响应格式: { list, total, pageSize, currentPage }

    Args:
        query: 角色列表查询参数（请求体）
        service: RBAC 服务实例（通过 DI 注入）

    Returns:
        Pure Admin 标准分页响应格式的角色列表
    """
    roles, total = await service.get_roles(query)

    # 转换为前端期望的字段格式
    role_list = []
    for role in roles:
        role_dict = {"id": role.id, "name": role.name, "code": role.code, "status": role.status, "remark": role.remark or "", "createTime": datetime_to_timestamp(role.createTime)}
        role_list.append(role_dict)

    return list_response(list_data=role_list, total=total, page_size=query.pageSize, current_page=query.pageNum)


@role_router.post("/create")
async def create_role(dto: RoleCreateDTO, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))):
    """创建角色接口。

    需要 role:manage 权限。
    前端调用: POST /api/system/role/create

    Args:
        dto: 角色创建数据
        service: RBAC 服务实例（通过 DI 注入）

    Returns:
        统一响应格式的角色信息，code=201
    """
    role = await service.create_role(dto)
    return success_response(data=role, message="角色创建成功", code=201)


@role_router.get("/{role_id}")
async def get_role(role_id: str, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:view"))):
    """获取角色详情接口。

    需要 role:view 权限。

    Args:
        role_id: 角色ID
        service: RBAC 服务实例（通过 DI 注入）

    Returns:
        统一响应格式的角色详情（含权限列表）
    """
    role = await service.get_role(role_id)
    return success_response(data=role)


@role_router.put("/{role_id}")
async def update_role(role_id: str, dto: RoleUpdateDTO, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))):
    """更新角色接口。

    需要 role:manage 权限。

    Args:
        role_id: 角色ID
        dto: 角色更新数据
        service: RBAC 服务实例（通过 DI 注入）

    Returns:
        统一响应格式的更新后角色信息
    """
    role = await service.update_role(role_id, dto)
    return success_response(data=role, message="角色更新成功")


@role_router.delete("/{role_id}")
async def delete_role(role_id: str, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))):
    """删除角色接口。

    需要 role:manage 权限。

    Args:
        role_id: 角色ID
        service: RBAC 服务实例（通过 DI 注入）

    Returns:
        统一响应格式的操作结果消息
    """
    await service.delete_role(role_id)
    return success_response(message="角色删除成功")


@role_router.post("/{role_id}/permissions")
async def assign_permissions(role_id: str, dto: AssignPermissionsDTO, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))):
    """为角色分配权限接口。

    需要 role:manage 权限。
    先清除角色的旧权限关联，再创建新的权限关联。

    Args:
        role_id: 角色ID
        dto: 权限分配数据（permissionIds列表）
        service: RBAC 服务实例（通过 DI 注入）

    Returns:
        统一响应格式的操作结果消息
    """
    await service.assign_permissions(role_id, dto.permissionIds)
    return success_response(message="权限分配成功")


@role_router.post("/{role_id}/menu")
async def assign_role_menu(role_id: str, data: dict, db: AsyncSession = Depends(get_db), role_repo: RoleRepository = Depends(get_role_repository), _: dict = Depends(require_permission("role:manage"))):
    """为角色分配菜单权限接口。

    需要 role:manage 权限。
    前端调用: POST /api/system/role/{id}/menu
    请求体: { menuIds: ["xxx", "yyy", "zzz"] }

    Args:
        role_id: 角色ID
        data: 菜单ID列表
        db: 数据库会话
        role_repo: 角色仓储实例（通过 DI 注入）

    Returns:
        统一响应格式的操作结果消息
    """
    menu_ids = data.get("menuIds", [])

    # 为角色分配菜单权限
    await role_repo.assign_menus_to_role(role_id, menu_ids)
    await db.commit()

    return success_response(message="菜单权限分配成功")
