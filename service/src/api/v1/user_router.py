"""System API - 用户管理路由模块。

提供用户管理相关的接口，包括用户增删改查、密码管理、状态管理等功能。
路由前缀: /api/system/user
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends

from src.api.common import format_user_list_row, list_response, success_response
from src.api.dependencies import get_current_user_id, get_user_service, require_permission
from src.application.dto.user_dto import AssignRoleDTO, BatchDeleteDTO, ChangePasswordDTO, ResetPasswordDTO, UpdateStatusDTO, UserCreateDTO, UserListQueryDTO, UserUpdateDTO
from src.application.services.user_service import UserService


class UserRouter(Routable):
    """用户管理路由类，提供用户增删改查、密码管理、状态管理等功能。"""

    @post("")
    async def get_user_list(self, query: UserListQueryDTO, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:view"))) -> dict:
        """获取用户列表接口（支持筛选和分页）。"""
        users, total = await service.get_users(query)
        user_list = [format_user_list_row(user.model_dump()) for user in users]
        return list_response(list_data=user_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/create", status_code=201)
    async def create_user(self, dto: UserCreateDTO, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:add"))) -> dict:
        """创建用户接口。"""
        user = await service.create_user(dto)
        return success_response(data=user, message="创建成功", code=201)

    @get("/info")
    async def get_current_user_info(self, user_id: str = Depends(get_current_user_id), service: UserService = Depends(get_user_service)) -> dict:
        """获取当前登录用户信息接口。"""
        user = await service.get_user(user_id)
        return success_response(data=user)

    @get("/{user_id}")
    async def get_user_detail(self, user_id: str, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:view"))) -> dict:
        """获取用户详情接口。"""
        user = await service.get_user(user_id)
        return success_response(data=user)

    @put("/{user_id}")
    async def update_user(self, user_id: str, dto: UserUpdateDTO, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:edit"))) -> dict:
        """更新用户接口。"""
        user = await service.update_user(user_id, dto)
        return success_response(data=user, message="更新成功")

    @delete("/{user_id}")
    async def delete_user(self, user_id: str, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:delete"))) -> dict:
        """删除用户接口。"""
        await service.delete_user(user_id)
        return success_response(message="删除成功")

    @post("/batch-delete")
    async def batch_delete_users(self, dto: BatchDeleteDTO, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:delete"))) -> dict:
        """批量删除用户接口。"""
        result = await service.batch_delete_users(dto.ids)
        return success_response(data=result, message="批量删除成功")

    @put("/{user_id}/reset-password")
    async def reset_user_password(self, user_id: str, dto: ResetPasswordDTO, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:edit"))) -> dict:
        """重置用户密码接口（管理员功能）。"""
        await service.reset_password(user_id, dto.newPassword)
        return success_response(message="密码重置成功")

    @put("/{user_id}/status")
    async def update_user_status(self, user_id: str, dto: UpdateStatusDTO, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:edit"))) -> dict:
        """更改用户状态接口。"""
        await service.update_status(user_id, dto.isActive)
        return success_response(message="状态更新成功")

    @post("/change-password")
    async def change_password(self, dto: ChangePasswordDTO, user_id: str = Depends(get_current_user_id), service: UserService = Depends(get_user_service)) -> dict:
        """修改当前用户密码接口。"""
        await service.change_password(user_id, dto)
        return success_response(message="密码修改成功")

    @post("/assign-role")
    async def assign_role(self, dto: AssignRoleDTO, service: UserService = Depends(get_user_service), _: dict = Depends(require_permission("user:edit"))) -> dict:
        """为用户分配角色接口。"""
        await service.assign_roles(dto.userId, dto.roleIds)
        return success_response(message="角色分配成功")
