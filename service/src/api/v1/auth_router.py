"""System API - 认证路由模块。

提供用户认证相关的接口，包括登录、注册、登出和令牌刷新等功能。
所有路由直接挂在 /api/system 路径下。
"""

from classy_fastapi import Routable, get, post
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import success_response
from src.api.dependencies import get_auth_service, get_current_active_user, get_menu_repository, get_role_repository, get_user_repository
from src.application.dto.auth_dto import LoginDTO, RefreshTokenDTO, RegisterDTO
from src.application.services.auth_service import AuthService
from src.domain.exceptions import UnauthorizedError
from src.infrastructure.database import get_db
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository


class AuthRouter(Routable):
    """认证管理路由类，提供登录、注册、令牌刷新等接口。"""

    @post("/login")
    async def login(self, dto: LoginDTO, service: AuthService = Depends(get_auth_service)) -> dict:
        """用户登录接口。"""
        result = await service.login(dto)
        return success_response(data=result, message="登录成功")

    @post("/register")
    async def register(self, dto: RegisterDTO, service: AuthService = Depends(get_auth_service)) -> dict:
        """用户注册接口。"""
        result = await service.register(dto)
        return success_response(data=result, message="注册成功")

    @post("/logout")
    async def logout(self, current_user: dict = Depends(get_current_active_user)) -> dict:
        """用户登出接口。"""
        return success_response(message="登出成功")

    @post("/refresh-token")
    async def refresh_token(self, dto: RefreshTokenDTO, service: AuthService = Depends(get_auth_service)) -> dict:
        """刷新访问令牌接口。"""
        result = await service.refresh_token(dto.refreshToken)
        return success_response(data=result, message="刷新成功")

    @get("/mine")
    async def get_mine(self, current_user: dict = Depends(get_current_active_user), user_repo: UserRepository = Depends(get_user_repository)) -> dict:
        """获取当前登录用户的个人信息。"""
        user = await user_repo.get_by_id(current_user["id"])
        if user is None:
            raise UnauthorizedError("用户不存在")
        return success_response(data={"avatar": user.avatar or "", "username": user.username, "nickname": user.nickname or user.username, "email": user.email or "", "phone": user.phone or "", "description": ""})

    @get("/mine-logs")
    async def get_mine_logs(self, current_user: dict = Depends(get_current_active_user)) -> dict:
        """获取当前用户的安全日志（stub 数据）。"""
        return success_response(data={"list": [], "total": 0, "pageSize": 10, "currentPage": 1})

    @get("/get-async-routes")
    async def get_async_routes(self, current_user: dict = Depends(get_current_active_user)) -> dict:
        """获取当前用户可访问的动态路由配置。"""
        system_management_router = {
            "path": "/system",
            "meta": {"icon": "ri:settings-3-line", "title": "menus.pureSysManagement", "rank": 10},
            "children": [
                {"path": "/system/user/index", "name": "SystemUser", "meta": {"icon": "ri:admin-line", "title": "menus.pureUser", "roles": ["admin"]}},
                {"path": "/system/role/index", "name": "SystemRole", "meta": {"icon": "ri:admin-fill", "title": "menus.pureRole", "roles": ["admin"]}},
                {"path": "/system/menu/index", "name": "SystemMenu", "meta": {"icon": "ep:menu", "title": "menus.pureSystemMenu", "roles": ["admin"]}},
                {"path": "/system/dept/index", "name": "SystemDept", "meta": {"icon": "ri:git-branch-line", "title": "menus.pureDept", "roles": ["admin"]}},
            ],
        }

        system_monitor_router = {
            "path": "/monitor",
            "meta": {"icon": "ep:monitor", "title": "menus.pureSysMonitor", "rank": 11},
            "children": [
                {"path": "/monitor/online-user", "component": "monitor/online/index", "name": "OnlineUser", "meta": {"icon": "ri:user-voice-line", "title": "menus.pureOnlineUser", "roles": ["admin"]}},
                {"path": "/monitor/login-logs", "component": "monitor/logs/login/index", "name": "LoginLog", "meta": {"icon": "ri:window-line", "title": "menus.pureLoginLog", "roles": ["admin"]}},
                {"path": "/monitor/operation-logs", "component": "monitor/logs/operation/index", "name": "OperationLog", "meta": {"icon": "ri:history-fill", "title": "menus.pureOperationLog", "roles": ["admin"]}},
                {"path": "/monitor/system-logs", "component": "monitor/logs/system/index", "name": "SystemLog", "meta": {"icon": "ri:file-search-line", "title": "menus.pureSystemLog", "roles": ["admin"]}},
            ],
        }

        permission_router = {
            "path": "/permission",
            "meta": {"title": "menus.purePermission", "icon": "ep:lollipop", "rank": 9},
            "children": [
                {"path": "/permission/page/index", "name": "PermissionPage", "meta": {"title": "menus.purePermissionPage", "roles": ["admin", "common"]}},
                {
                    "path": "/permission/button",
                    "meta": {"title": "menus.purePermissionButton", "roles": ["admin", "common"]},
                    "children": [
                        {"path": "/permission/button/router", "component": "permission/button/index", "name": "PermissionButtonRouter", "meta": {"title": "menus.purePermissionButtonRouter", "auths": ["permission:btn:add", "permission:btn:edit", "permission:btn:delete"]}},
                        {"path": "/permission/button/login", "component": "permission/button/perms", "name": "PermissionButtonLogin", "meta": {"title": "menus.purePermissionButtonLogin"}},
                    ],
                },
            ],
        }

        return success_response(data=[system_management_router, system_monitor_router, permission_router])

    @get("/list-all-role")
    async def list_all_roles(self, role_repo: RoleRepository = Depends(get_role_repository), current_user: dict = Depends(get_current_active_user)) -> dict:
        """获取所有角色简单列表。"""
        roles = await role_repo.get_all(page_num=1, page_size=1000)
        return success_response(data=[{"id": r.id, "name": r.name} for r in roles])

    @post("/list-role-ids")
    async def list_role_ids(self, data: dict, role_repo: RoleRepository = Depends(get_role_repository), current_user: dict = Depends(get_current_active_user)) -> dict:
        """根据用户ID获取对应角色ID列表。"""
        user_id = data.get("userId")
        if not user_id:
            return {"code": 10001, "message": "请求参数缺失或格式不正确", "data": []}
        roles = await role_repo.get_user_roles(str(user_id))
        return success_response(data=[r.id for r in roles])

    @post("/role-menu")
    async def get_role_menu(self, current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db), menu_repo: MenuRepository = Depends(get_menu_repository)) -> dict:
        """获取角色菜单权限树。"""
        all_menus = await menu_repo.get_all()
        menu_list = []
        for menu in all_menus:
            menu_dict = {"parentId": int(menu.parent_id) if menu.parent_id else 0, "id": int(menu.id) if menu.id.isdigit() else menu.id, "menuType": 0, "title": menu.title or menu.name}
            menu_list.append(menu_dict)
        return success_response(data=menu_list)

    @post("/role-menu-ids")
    async def get_role_menu_ids(self, data: dict, current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db), menu_repo: MenuRepository = Depends(get_menu_repository), role_repo: RoleRepository = Depends(get_role_repository)) -> dict:
        """根据角色ID获取菜单ID列表。"""
        role_id = data.get("id")
        if not role_id:
            return success_response(data=[])
        role = await role_repo.get_by_id(str(role_id))
        if role and role.code == "admin":
            all_menus = await menu_repo.get_all()
            menu_ids = [m.id for m in all_menus]
            return success_response(data=menu_ids)
        menu_ids = await role_repo.get_role_menu_ids(str(role_id))
        return success_response(data=menu_ids)
