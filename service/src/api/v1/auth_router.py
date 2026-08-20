"""System API - 认证路由模块。

提供用户认证相关的接口，包括登录、注册、登出、令牌刷新、动态路由等功能。
所有路由直接挂在 /api/system 路径下。
"""

from classy_fastapi import Routable, get, post
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials

from src.api.common import list_response, success_response
from src.api.common.response_schemas import ApiResponse, PaginatedResponse
from src.api.dependencies import (
    get_auth_service,
    get_current_active_user,
    get_menu_service,
    get_role_service,
    get_user_service,
    security_scheme,
)
from src.application.dto.auth_dto import (
    LoginDTO,
    MineUserDTO,
    RefreshTokenDTO,
    RegisterDTO,
    RoleIdRequestDTO,
    RoleMenuItemDTO,
    UserIdRequestDTO,
)
from src.application.services.auth_service import AuthService
from src.application.services.menu_service import MenuService
from src.application.services.role_service import RoleService
from src.application.services.user_service import UserService
from src.domain.entities.user import UserEntity
from src.domain.error_messages import ErrorMessages as EM
from src.domain.exceptions import UnauthorizedError


class AuthRouter(Routable):
    """认证管理路由类，提供登录、注册、令牌刷新、动态路由等接口。"""

    @post("/login", response_model=ApiResponse[dict])
    async def login(self, request: Request, dto: LoginDTO, service: AuthService = Depends(get_auth_service)) -> dict:
        """用户登录接口。"""
        result = await service.login(dto)
        return success_response(data=result, message="登录成功")

    @post("/register", response_model=ApiResponse[dict])
    async def register(
        self, request: Request, dto: RegisterDTO, service: AuthService = Depends(get_auth_service)
    ) -> dict:
        """用户注册接口。"""
        result = await service.register(dto)
        return success_response(data=result, message="注册成功")

    @post("/logout", response_model=ApiResponse[None])
    async def logout(
        self,
        current_user: UserEntity = Depends(get_current_active_user),
        service: AuthService = Depends(get_auth_service),
        credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    ) -> dict:
        """用户登出接口。将 access_token 写入黑名单。"""
        token = credentials.credentials
        await service.logout(token)
        return success_response(message="登出成功")

    @post("/refresh-token", response_model=ApiResponse[dict])
    async def refresh_token(self, dto: RefreshTokenDTO, service: AuthService = Depends(get_auth_service)) -> dict:
        """刷新访问令牌接口。"""
        result = await service.refresh_token(dto.refreshToken)
        return success_response(data=result, message="刷新成功")

    @get("/mine", response_model=ApiResponse[dict])
    async def get_mine(
        self,
        current_user: UserEntity = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service),
    ) -> dict:
        """获取当前登录用户的个人信息。"""
        user = await user_service.get_user_by_id(current_user.id)
        if user is None:
            raise UnauthorizedError(EM.USER_NOT_FOUND)
        data = MineUserDTO(
            avatar=user.avatar or "",
            username=user.username,
            nickname=user.nickname or user.username,
            email=user.email or "",
            phone=user.phone or "",
            description=user.description or "",
        )
        return success_response(data=data.model_dump())

    @get("/mine-logs", response_model=PaginatedResponse[dict])
    async def get_mine_logs(self, current_user: UserEntity = Depends(get_current_active_user)) -> dict:
        """获取当前用户的安全日志（stub 数据）。"""
        return list_response(list_data=[], total=0)

    @get("/get-async-routes", response_model=ApiResponse[list[dict]])
    async def get_async_routes(
        self,
        current_user: UserEntity = Depends(get_current_active_user),
        service: AuthService = Depends(get_auth_service),
    ) -> dict:
        """获取当前用户可访问的动态路由配置。"""
        tree = await service.get_async_routes(current_user.id)
        return success_response(data=tree)

    @get("/list-all-role", response_model=ApiResponse[list[dict]])
    async def list_all_roles(
        self,
        role_service: RoleService = Depends(get_role_service),
        current_user: UserEntity = Depends(get_current_active_user),
    ) -> dict:
        """获取所有角色简单列表。"""
        roles = await role_service.get_all_simple_roles()
        return success_response(data=roles)

    @post("/list-role-ids", response_model=ApiResponse[list[str]])
    async def list_role_ids(
        self,
        dto: UserIdRequestDTO,
        service: AuthService = Depends(get_auth_service),
        current_user: UserEntity = Depends(get_current_active_user),
    ) -> dict:
        """根据用户ID获取对应角色ID列表。"""
        role_ids = await service.get_user_role_ids(str(dto.userId))
        return success_response(data=role_ids)

    @post("/role-menu", response_model=ApiResponse[list[dict]])
    async def get_role_menu(
        self,
        current_user: UserEntity = Depends(get_current_active_user),
        menu_service: MenuService = Depends(get_menu_service),
    ) -> dict:
        """获取角色菜单权限树。"""
        all_menus = await menu_service.get_all_menus_raw()
        menu_list: list[dict] = []
        for menu in all_menus:
            parent_id = int(menu.parent_id) if menu.parent_id and menu.parent_id.isdigit() else (menu.parent_id or 0)
            menu_id = int(menu.id) if menu.id.isdigit() else menu.id
            title = menu.meta.title if menu.meta else (menu.name or "")
            item = RoleMenuItemDTO(parentId=parent_id, id=menu_id, menuType=menu.menu_type, title=title)
            menu_list.append(item.model_dump())
        return success_response(data=menu_list)

    @post("/role-menu-ids", response_model=ApiResponse[list[str]])
    async def get_role_menu_ids(
        self,
        dto: RoleIdRequestDTO,
        service: AuthService = Depends(get_auth_service),
        current_user: UserEntity = Depends(get_current_active_user),
    ) -> dict:
        """根据角色ID获取菜单ID列表。"""
        menu_ids = await service.get_role_menu_ids(str(dto.id))
        return success_response(data=menu_ids)
