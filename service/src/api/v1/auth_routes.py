"""System API - 认证路由模块。

提供用户认证相关的接口，包括登录、注册、登出和令牌刷新等功能。
所有路由直接挂在 /api/system 路径下。
"""

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import success_response
from src.api.dependencies import get_auth_service, get_current_active_user, get_menu_repository, get_role_repository, get_user_repository
from src.application.dto.auth_dto import LoginDTO, RefreshTokenDTO, RegisterDTO
from src.application.services.auth_service import AuthService
from src.core.exceptions import UnauthorizedError
from src.infrastructure.database import get_db
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository

router = APIRouter()


@router.post("/login")
async def login(dto: LoginDTO, service: AuthService = Depends(get_auth_service)):
    """用户登录接口。

    验证用户凭据并返回完整的登录信息，包括访问令牌、刷新令牌、用户信息、角色和权限。

    Args:
        dto: 登录请求数据，包含用户名和密码
        service: 认证服务实例（通过 DI 注入）

    Returns:
        dict: 统一格式的登录响应，包含 accessToken, expires, refreshToken, userInfo, roles, permissions
    """
    result = await service.login(dto)
    return success_response(data=result, message="登录成功")


@router.post("/register")
async def register(dto: RegisterDTO, service: AuthService = Depends(get_auth_service)):
    """用户注册接口。

    创建新用户账号。

    Args:
        dto: 注册请求数据，包含用户名、密码等信息
        service: 认证服务实例（通过 DI 注入）

    Returns:
        dict: 统一格式的注册响应，包含新创建用户的基本信息
    """
    result = await service.register(dto)
    return success_response(data=result, message="注册成功")


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_active_user)):
    """用户登出接口。

    JWT 无状态认证，服务端无需特殊处理，客户端只需删除本地令牌。

    Args:
        current_user: 当前登录用户信息

    Returns:
        dict: 统一格式的登出成功响应
    """
    return success_response(message="登出成功")


@router.post("/refresh-token")
async def refresh_token(dto: RefreshTokenDTO, service: AuthService = Depends(get_auth_service)):
    """刷新访问令牌接口。

    使用有效的刷新令牌获取新的访问令牌。

    Args:
        dto: 刷新令牌请求数据
        service: 认证服务实例（通过 DI 注入）

    Returns:
        dict: 统一格式的刷新响应，包含 accessToken, expires, refreshToken
    """
    result = await service.refresh_token(dto.refreshToken)
    return success_response(data=result, message="刷新成功")


@router.get("/mine")
async def get_mine(current_user: dict = Depends(get_current_active_user), user_repo: UserRepository = Depends(get_user_repository)):
    """获取当前登录用户的个人信息。

    Args:
        current_user: 当前登录用户信息
        user_repo: 用户仓储实例（通过 DI 注入）

    Returns:
        dict: 统一格式的用户信息响应，包含 avatar, username, nickname, email, phone, description
    """
    user = await user_repo.get_by_id(current_user["id"])
    if user is None:
        raise UnauthorizedError("用户不存在")
    return success_response(data={"avatar": user.avatar or "", "username": user.username, "nickname": user.nickname or user.username, "email": user.email or "", "phone": user.phone or "", "description": ""})


@router.get("/mine-logs")
async def get_mine_logs(current_user: dict = Depends(get_current_active_user)):
    """获取当前用户的安全日志（stub 数据）。

    Args:
        current_user: 当前登录用户信息

    Returns:
        dict: 统一格式的安全日志响应，包含分页的日志列表
    """
    return success_response(data={"list": [], "total": 0, "pageSize": 10, "currentPage": 1})


@router.get("/get-async-routes")
async def get_async_routes(current_user: dict = Depends(get_current_active_user)):
    """获取当前用户可访问的动态路由配置。

    根据用户角色返回对应的菜单路由配置，前端用于动态加载菜单。

    Args:
        current_user: 当前登录用户信息

    Returns:
        dict: 统一格式的路由配置响应，包含路由数组
    """
    # 系统管理路由
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

    # 系统监控路由
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

    # 权限管理路由
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


# =============================================================================
# 系统管理辅助接口
# =============================================================================


@router.get("/list-all-role")
async def list_all_roles(role_repo: RoleRepository = Depends(get_role_repository), current_user: dict = Depends(get_current_active_user)):
    """获取所有角色简单列表。

    前端调用: GET /api/system/list-all-role
    用于用户管理中的角色分配下拉选择。
    """
    # 获取所有角色（不分页）
    roles = await role_repo.get_all(page_num=1, page_size=1000)
    return success_response(data=[{"id": r.id, "name": r.name} for r in roles])


@router.post("/list-role-ids")
async def list_role_ids(data: dict, role_repo: RoleRepository = Depends(get_role_repository), current_user: dict = Depends(get_current_active_user)):
    """根据用户ID获取对应角色ID列表。

    前端调用: POST /api/system/list-role-ids
    请求体: { "userId": 1 }
    """
    user_id = data.get("userId")
    if not user_id:
        return {"code": 10001, "message": "请求参数缺失或格式不正确", "data": []}

    roles = await role_repo.get_user_roles(str(user_id))
    return success_response(data=[r.id for r in roles])


@router.post("/role-menu")
async def get_role_menu(current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db), menu_repo: MenuRepository = Depends(get_menu_repository)):
    """获取角色菜单权限树。

    前端调用: POST /api/system/role-menu
    返回菜单权限树形结构，用于角色权限分配。
    """
    all_menus = await menu_repo.get_all(db)

    # 转换为前端期望的格式
    menu_list = []
    for menu in all_menus:
        menu_dict = {
            "parentId": int(menu.parent_id) if menu.parent_id else 0,
            "id": int(menu.id) if menu.id.isdigit() else menu.id,
            "menuType": 0,  # 0-菜单, 1-iframe, 2-外链, 3-按钮
            "title": menu.title or menu.name,
        }
        menu_list.append(menu_dict)

    return success_response(data=menu_list)


@router.post("/role-menu-ids")
async def get_role_menu_ids(data: dict, current_user: dict = Depends(get_current_active_user), db: AsyncSession = Depends(get_db), menu_repo: MenuRepository = Depends(get_menu_repository), role_repo: RoleRepository = Depends(get_role_repository)):
    """根据角色ID获取菜单ID列表。

    前端调用: POST /api/system/role-menu-ids
    请求体: { "id": "xxx" }
    返回角色已分配的菜单ID列表。
    """
    role_id = data.get("id")
    if not role_id:
        return success_response(data=[])

    # 如果是超级管理员角色（code=admin），返回所有菜单
    role = await role_repo.get_by_id(str(role_id))
    if role and role.code == "admin":
        all_menus = await menu_repo.get_all(db)
        menu_ids = [m.id for m in all_menus]
        return success_response(data=menu_ids)

    # 其他角色返回已分配的菜单ID列表
    menu_ids = await role_repo.get_role_menu_ids(str(role_id))
    return success_response(data=menu_ids)
