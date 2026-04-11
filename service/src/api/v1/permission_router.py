"""System API - 权限管理路由模块。

提供权限管理相关的接口，包括权限增删改查等功能。
路由前缀: /api/system/permission
"""

from fastapi import Depends, Query

from src.api.common import page_response, success_response
from src.api.dependencies import get_permission_service, require_permission
from src.application.dto.permission_dto import PermissionCreateDTO, PermissionListQueryDTO
from src.application.services.permission_service import PermissionService

from classy_fastapi import Routable, delete, get, post


class PermissionRouter(Routable):
    """权限管理路由类，提供权限增删改查等功能。"""

    @get("/list")
    async def get_permission_list(
        self,
        pageNum: int = Query(1, ge=1, description="页码"),
        pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
        permissionName: str = Query(None, description="权限名称"),
        service: PermissionService = Depends(get_permission_service),
        _: dict = Depends(require_permission("permission:view")),
    ) -> dict:
        """获取权限列表接口（分页）。"""
        query = PermissionListQueryDTO(pageNum=pageNum, pageSize=pageSize, permissionName=permissionName)
        permissions, total = await service.get_permissions(query)
        return page_response(rows=permissions, total=total, page_num=query.pageNum, page_size=query.pageSize)

    @post("/")
    async def create_permission(
        self,
        dto: PermissionCreateDTO,
        service: PermissionService = Depends(get_permission_service),
        _: dict = Depends(require_permission("permission:manage")),
    ) -> dict:
        """创建权限接口。"""
        permission = await service.create_permission(dto)
        return success_response(data=permission, message="权限创建成功", code=201)

    @delete("/{permission_id}")
    async def delete_permission(
        self,
        permission_id: str,
        service: PermissionService = Depends(get_permission_service),
        _: dict = Depends(require_permission("permission:manage")),
    ) -> dict:
        """删除权限接口。"""
        await service.delete_permission(permission_id)
        return success_response(message="权限删除成功")
