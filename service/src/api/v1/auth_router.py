"""System API - 认证路由模块。

提供用户认证相关的接口，包括登录、注册、登出、令牌刷新、动态路由等功能。
所有路由直接挂在 /api/system 路径下。
"""

from classy_fastapi import Routable, get, post
from fastapi import Depends

from src.api.common import success_response
from src.api.dependencies import get_auth_service, get_current_active_user, get_menu_repository, get_role_repository, get_user_repository
from src.application.dto.auth_dto import LoginDTO, RefreshTokenDTO, RegisterDTO
from src.application.services.auth_service import AuthService
from src.domain.entities.menu import MenuEntity
from src.domain.exceptions import UnauthorizedError
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository


class AuthRouter(Routable):
    """认证管理路由类，提供登录、注册、令牌刷新、动态路由等接口。"""

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
        return success_response(data={"avatar": user.avatar or "", "username": user.username, "nickname": user.nickname or user.username, "email": user.email or "", "phone": user.phone or "", "description": user.description or ""})

    @get("/mine-logs")
    async def get_mine_logs(self, current_user: dict = Depends(get_current_active_user)) -> dict:
        """获取当前用户的安全日志（stub 数据）。"""
        return success_response(data={"list": [], "total": 0, "pageSize": 10, "currentPage": 1})

    @get("/get-async-routes")
    async def get_async_routes(self, current_user: dict = Depends(get_current_active_user), menu_repo: MenuRepository = Depends(get_menu_repository)) -> dict:
        """获取当前用户可访问的动态路由配置。

        从数据库读取菜单数据，构建前端路由结构。
        menu_type: 0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限
        """
        all_menus = await menu_repo.get_all()
        # 过滤掉 PERMISSION 类型（menu_type=2），仅返回目录和页面路由
        route_menus = [m for m in all_menus if m.menu_type != MenuEntity.PERMISSION]
        tree = self._build_route_tree(route_menus, None)
        return success_response(data=tree)

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
    async def get_role_menu(self, current_user: dict = Depends(get_current_active_user), menu_repo: MenuRepository = Depends(get_menu_repository)) -> dict:
        """获取角色菜单权限树。"""
        all_menus = await menu_repo.get_all()
        menu_list = []
        for menu in all_menus:
            menu_dict = {"parentId": int(menu.parent_id) if menu.parent_id and menu.parent_id.isdigit() else (menu.parent_id or 0), "id": int(menu.id) if menu.id.isdigit() else menu.id, "menuType": menu.menu_type, "title": menu.meta.title if menu.meta else (menu.name or "")}
            menu_list.append(menu_dict)
        return success_response(data=menu_list)

    @post("/role-menu-ids")
    async def get_role_menu_ids(self, data: dict, current_user: dict = Depends(get_current_active_user), menu_repo: MenuRepository = Depends(get_menu_repository), role_repo: RoleRepository = Depends(get_role_repository)) -> dict:
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

    def _build_route_tree(self, menus: list, parent_id: str | None) -> list[dict]:
        """根据菜单数据构建前端路由树结构。

        将 Menu+MenuMeta 组合为前端 get-async-routes 需要的格式。
        menu_type=0 为目录，menu_type=1 为页面。
        """
        tree = []
        for menu in menus:
            if menu.parent_id == parent_id:
                node = {"path": menu.path or "", "name": menu.name or "", "rank": menu.rank, "meta": self._build_meta(menu)}
                if menu.component:
                    node["component"] = menu.component
                children = self._build_route_tree(menus, menu.id)
                if children:
                    node["children"] = children
                tree.append(node)
        return tree

    def _build_meta(self, menu) -> dict:
        """从 Menu 的 meta 关系构建 meta 字典。"""
        meta = {"title": menu.name or ""}
        # 如果有 MenuMeta 关联数据
        if menu.meta:
            m = menu.meta
            if m.title:
                meta["title"] = m.title
            if m.icon:
                meta["icon"] = m.icon
            if m.r_svg_name:
                meta["rSvgName"] = m.r_svg_name
            if m.is_show_menu == 0:
                meta["showLink"] = False
            if m.is_show_parent == 1:
                meta["showParent"] = True
            if m.is_keepalive == 1:
                meta["keepAlive"] = True
            if m.frame_url:
                meta["frameSrc"] = m.frame_url
            if m.frame_loading == 0:
                meta["frameLoading"] = False
            if m.transition_enter:
                meta["enterTransition"] = m.transition_enter
            if m.transition_leave:
                meta["leaveTransition"] = m.transition_leave
            if m.is_hidden_tag == 1:
                meta["hiddenTag"] = True
            if m.fixed_tag == 1:
                meta["fixedTag"] = True
            if m.dynamic_level > 0:
                meta["dynamicLevel"] = m.dynamic_level
        return meta
