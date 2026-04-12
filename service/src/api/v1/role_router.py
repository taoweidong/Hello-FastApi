"""System API - 角色管理路由模块。

提供角色管理相关的接口，包括角色增删改查、菜单分配等功能。
路由前缀: /api/system/role
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import list_response, success_response
from src.api.dependencies import get_role_repository, get_role_service, require_permission
from src.application.dto.role_dto import AssignMenusDTO, RoleCreateDTO, RoleListQueryDTO, RoleUpdateDTO
from src.application.services.role_service import RoleService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.role_repository import RoleRepository


class RoleRouter(Routable):
    """角色管理路由类，提供角色增删改查、菜单分配等功能。"""

    @post("")
    async def get_role_list(self, query: RoleListQueryDTO, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:view"))) -> dict:
        """获取角色列表接口（分页）。"""
        roles, total = await service.get_roles(query)
        role_list = []
        for role in roles:
            role_dict = {
                "id": role.id,
                "name": role.name,
                "code": role.code,
                "isActive": role.isActive,
                "description": role.description or "",
                "menus": role.menus if role.menus else [],
                "createdTime": role.createdTime.isoformat() if role.createdTime else None,
            }
            role_list.append(role_dict)
        return list_response(list_data=role_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/create")
    async def create_role(self, dto: RoleCreateDTO, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))) -> dict:
        """创建角色接口。"""
        role = await service.create_role(dto)
        return success_response(data=role, message="角色创建成功", code=201)

    @get("/{role_id}")
    async def get_role(self, role_id: str, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:view"))) -> dict:
        """获取角色详情接口。"""
        role = await service.get_role(role_id)
        return success_response(data=role)

    @put("/{role_id}")
    async def update_role(self, role_id: str, dto: RoleUpdateDTO, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))) -> dict:
        """更新角色接口。"""
        role = await service.update_role(role_id, dto)
        return success_response(data=role, message="角色更新成功")

    @delete("/{role_id}")
    async def delete_role(self, role_id: str, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))) -> dict:
        """删除角色接口。"""
        await service.delete_role(role_id)
        return success_response(message="角色删除成功")

    @put("/{role_id}/status")
    async def update_role_status(self, role_id: str, data: dict, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))) -> dict:
        """更新角色状态接口。"""
        is_active = data.get("isActive")
        if is_active is None:
            return success_response(message="状态值不能为空")
        dto = RoleUpdateDTO(isActive=int(is_active))
        await service.update_role(role_id, dto)
        return success_response(message="状态更新成功")

    @post("/{role_id}/menus")
    async def assign_menus(self, role_id: str, dto: AssignMenusDTO, service: RoleService = Depends(get_role_service), _: dict = Depends(require_permission("role:manage"))) -> dict:
        """为角色分配菜单权限接口。"""
        await service.assign_menus(role_id, dto.menuIds)
        return success_response(message="菜单权限分配成功")

    @post("/{role_id}/menu")
    async def assign_role_menu(self, role_id: str, data: dict, db: AsyncSession = Depends(get_db), role_repo: RoleRepository = Depends(get_role_repository), _: dict = Depends(require_permission("role:manage"))) -> dict:
        """为角色分配菜单权限接口（兼容旧前端）。"""
        menu_ids = data.get("menuIds", [])
        await role_repo.assign_menus_to_role(role_id, menu_ids)
        await db.commit()
        return success_response(message="菜单权限分配成功")
