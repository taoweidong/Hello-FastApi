"""System API - 权限管理路由模块。

提供权限管理相关的接口，包括权限增删改查等功能。
路由前缀: /api/system/permission
"""

from fastapi import APIRouter, Depends, Query

from src.api.common import page_response, success_response
from src.api.dependencies import get_permission_service, require_permission
from src.application.dto.permission_dto import PermissionCreateDTO, PermissionListQueryDTO
from src.application.services.permission_service import PermissionService

permission_router = APIRouter()


@permission_router.get("/list")
async def get_permission_list(
    pageNum: int = Query(1, ge=1, description="页码"), pageSize: int = Query(10, ge=1, le=100, description="每页条数"), permissionName: str = Query(None, description="权限名称"), service: PermissionService = Depends(get_permission_service), _: dict = Depends(require_permission("permission:view"))
):
    """获取权限列表接口（分页）。

    需要 permission:view 权限。

    Args:
        pageNum: 页码
        pageSize: 每页条数
        permissionName: 权限名称（模糊查询）
        service: 权限服务实例（通过 DI 注入）

    Returns:
        分页响应格式的权限列表
    """
    # 构建DTO
    query = PermissionListQueryDTO(pageNum=pageNum, pageSize=pageSize, permissionName=permissionName)

    permissions, total = await service.get_permissions(query)
    return page_response(rows=permissions, total=total, page_num=query.pageNum, page_size=query.pageSize)


@permission_router.post("/")
async def create_permission(dto: PermissionCreateDTO, service: PermissionService = Depends(get_permission_service), _: dict = Depends(require_permission("permission:manage"))):
    """创建权限接口。

    需要 permission:manage 权限。

    Args:
        dto: 权限创建数据
        service: 权限服务实例（通过 DI 注入）

    Returns:
        统一响应格式的权限信息，code=201
    """
    permission = await service.create_permission(dto)
    return success_response(data=permission, message="权限创建成功", code=201)


@permission_router.delete("/{permission_id}")
async def delete_permission(permission_id: str, service: PermissionService = Depends(get_permission_service), _: dict = Depends(require_permission("permission:manage"))):
    """删除权限接口。

    需要 permission:manage 权限。

    Args:
        permission_id: 权限ID
        service: 权限服务实例（通过 DI 注入）

    Returns:
        统一响应格式的操作结果消息
    """
    await service.delete_permission(permission_id)
    return success_response(message="权限删除成功")
