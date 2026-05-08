"""System API - 认证路由模块。

提供用户认证相关的接口，包括登录、注册、登出、令牌刷新、动态路由等功能。
所有路由直接挂在 /api/system 路径下。
"""

from classy_fastapi import Routable, get, post
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials

from src.api.common import list_response, success_response
from src.api.dependencies import (
    get_auth_service,
    get_current_active_user,
    get_menu_repository,
    get_role_repository,
    get_user_repository,
    security_scheme,
)
from src.application.dto.auth_dto import LoginDTO, RefreshTokenDTO, RegisterDTO
from src.application.services.auth_service import AuthService
from src.domain.exceptions import UnauthorizedError
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository


class AuthRouter(Routable):
    """认证管理路由类，提供登录、注册、令牌刷新、动态路由等接口。"""

    @post("/login")
    async def login(self, request: Request, dto: LoginDTO, service: AuthService = Depends(get_auth_service)) -> dict:
        """用户登录接口。"""
        result = await service.login(dto)
        return success_response(data=result, message="登录成功")

    @post("/register")
    async def register(
        self, request: Request, dto: RegisterDTO, service: AuthService = Depends(get_auth_service)
    ) -> dict:
        """用户注册接口。"""
        result = await service.register(dto)
        return success_response(data=result, message="注册成功")

    @post("/logout")
    async def logout(
        self,
        current_user: dict = Depends(get_current_active_user),
        service: AuthService = Depends(get_auth_service),
        credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    ) -> dict:
        """用户登出接口。将 access_token 写入黑名单。"""
        token = credentials.credentials
        await service.logout(token)
        return success_response(message="登出成功")

    @post("/refresh-token")
    async def refresh_token(self, dto: RefreshTokenDTO, service: AuthService = Depends(get_auth_service)) -> dict:
        """刷新访问令牌接口。"""
        result = await service.refresh_token(dto.refreshToken)
        return success_response(data=result, message="刷新成功")

    @get("/mine")
    async def get_mine(
        self,
        current_user: dict = Depends(get_current_active_user),
        user_repo: UserRepository = Depends(get_user_repository),
    ) -> dict:
        """获取当前登录用户的个人信息。"""
        user = await user_repo.get_by_id(current_user["id"])
        if user is None:
            raise UnauthorizedError("用户不存在")
        return success_response(
            data={
                "avatar": user.avatar or "",
                "username": user.username,
                "nickname": user.nickname or user.username,
                "email": user.email or "",
                "phone": user.phone or "",
                "description": user.description or "",
            }
        )

    @get("/mine-logs")
    async def get_mine_logs(self, current_user: dict = Depends(get_current_active_user)) -> dict:
        """获取当前用户的安全日志（stub 数据）。"""
        return list_response(list_data=[], total=0)

    @get("/get-async-routes")
    async def get_async_routes(
        self,
        current_user: dict = Depends(get_current_active_user),
        service: AuthService = Depends(get_auth_service),
    ) -> dict:
        """获取当前用户可访问的动态路由配置。"""
        tree = await service.get_async_routes(current_user["id"])
        return success_response(data=tree)

    @get("/list-all-role")
    async def list_all_roles(
        self,
        role_repo: RoleRepository = Depends(get_role_repository),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """获取所有角色简单列表。"""
        roles = await role_repo.get_all(page_num=1, page_size=1000)
        return success_response(data=[{"id": r.id, "name": r.name} for r in roles])

    @post("/list-role-ids")
    async def list_role_ids(
        self,
        data: dict,
        service: AuthService = Depends(get_auth_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """根据用户ID获取对应角色ID列表。"""
        user_id = data.get("userId")
        if not user_id:
            return {"code": 10001, "message": "请求参数缺失或格式不正确", "data": []}
        role_ids = await service.get_user_role_ids(str(user_id))
        return success_response(data=role_ids)

    @post("/role-menu")
    async def get_role_menu(
        self,
        current_user: dict = Depends(get_current_active_user),
        menu_repo: MenuRepository = Depends(get_menu_repository),
    ) -> dict:
        """获取角色菜单权限树。"""
        all_menus = await menu_repo.get_all()
        menu_list = []
        for menu in all_menus:
            menu_dict = {
                "parentId": int(menu.parent_id)
                if menu.parent_id and menu.parent_id.isdigit()
                else (menu.parent_id or 0),
                "id": int(menu.id) if menu.id.isdigit() else menu.id,
                "menuType": menu.menu_type,
                "title": menu.meta.title if menu.meta else (menu.name or ""),
            }
            menu_list.append(menu_dict)
        return success_response(data=menu_list)

    @post("/role-menu-ids")
    async def get_role_menu_ids(
        self,
        data: dict,
        service: AuthService = Depends(get_auth_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """根据角色ID获取菜单ID列表。"""
        role_id = data.get("id")
        if not role_id:
            return success_response(data=[])
        menu_ids = await service.get_role_menu_ids(str(role_id))
        return success_response(data=menu_ids)
