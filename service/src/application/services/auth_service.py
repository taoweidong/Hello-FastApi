"""应用层 - 认证服务。"""

from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.auth_dto import LoginDTO, RegisterDTO
from src.config.settings import settings
from src.domain.exceptions import BusinessError, NotFoundError, UnauthorizedError
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService
from src.infrastructure.database.models import User


class AuthService:
    """认证操作的应用服务。"""

    def __init__(self, session: AsyncSession, user_repo: UserRepositoryInterface, role_repo: RoleRepositoryInterface, menu_repo: MenuRepositoryInterface, token_service: TokenService, password_service: PasswordService):
        self.session = session
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.menu_repo = menu_repo
        self.token_service = token_service
        self.password_service = password_service

    async def login(self, dto: LoginDTO) -> dict:
        """认证用户并返回完整登录信息。"""
        # 1. 验证用户名密码
        user = await self.user_repo.get_by_username(dto.username)
        if user is None:
            raise UnauthorizedError("用户名或密码错误")

        if not self.password_service.verify_password(dto.password, user.password):
            raise UnauthorizedError("用户名或密码错误")

        # 2. 检查用户状态
        if not user.is_active:
            raise UnauthorizedError("用户账号已被禁用")

        # 3. 生成令牌
        token_data = {"sub": user.id, "username": user.username}
        access_token = self.token_service.create_access_token(token_data)
        refresh_token = self.token_service.create_refresh_token(token_data)

        # 4. 查询用户角色和菜单权限
        if user.is_superuser:
            user_roles = await self.role_repo.get_all(page_num=1, page_size=100)
            user_menus = await self.menu_repo.get_all(self.session)
        else:
            user_roles = await self.role_repo.get_user_roles(user.id)
            # 收集用户所有角色关联的菜单
            menu_ids = set()
            user_menus = []
            for role in user_roles:
                role_menus = await self.role_repo.get_role_menus(role.id)
                for menu in role_menus:
                    if menu.id not in menu_ids:
                        menu_ids.add(menu.id)
                        user_menus.append(menu)

        # 5. 构建菜单名称列表（用于前端按钮权限 hasAuth 检查）
        menu_names = [m.name for m in user_menus if m.menu_type == 2]  # PERMISSION类型

        # 6. 计算过期时间
        expires_time = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_str = expires_time.strftime("%Y/%m/%d %H:%M:%S")

        # 7. 构建扁平结构的登录响应
        return {
            "avatar": user.avatar or "",
            "username": user.username,
            "nickname": user.nickname or user.username,
            "roles": [role.name for role in user_roles],
            "permissions": menu_names,  # 用菜单name替代权限code
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expires": expires_str,
        }

    async def register(self, dto: RegisterDTO) -> dict:
        """用户注册。"""
        existing_user = await self.user_repo.get_by_username(dto.username)
        if existing_user is not None:
            raise BusinessError("用户名已存在")

        hashed_password = self.password_service.hash_password(dto.password)

        new_user = User(username=dto.username, password=hashed_password, nickname=dto.nickname, email=dto.email or "", phone=dto.phone or "", is_active=1)
        await self.user_repo.create(new_user)
        await self.session.flush()
        created_user = await self.user_repo.get_by_username(dto.username)
        if created_user is None:
            raise NotFoundError("注册成功但无法加载用户")

        return {"id": created_user.id, "username": created_user.username, "nickname": created_user.nickname, "email": created_user.email, "phone": created_user.phone, "is_active": created_user.is_active}

    async def refresh_token(self, refresh_token: str) -> dict:
        """使用刷新令牌刷新访问令牌。"""
        payload = self.token_service.decode_token(refresh_token)
        if payload is None:
            raise UnauthorizedError("无效的刷新令牌")

        if not self.token_service.verify_token_type(payload, "refresh"):
            raise UnauthorizedError("无效的令牌类型")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("无效的刷新令牌")

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("用户不存在或已被禁用")

        token_data = {"sub": user.id, "username": user.username}
        new_access_token = self.token_service.create_access_token(token_data)
        new_refresh_token = self.token_service.create_refresh_token(token_data)

        expires_time = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_str = expires_time.strftime("%Y/%m/%d %H:%M:%S")

        return {"accessToken": new_access_token, "refreshToken": new_refresh_token, "expires": expires_str}

    async def get_async_routes(self, user_id: str) -> list[dict]:
        """根据用户角色获取动态路由（从数据库Menu+MenuMeta构建）。

        Args:
            user_id: 用户ID

        Returns:
            前端路由配置列表
        """
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return []

        # 获取用户的菜单（仅DIRECTORY和MENU类型）
        if user.is_superuser:
            all_menus = await self.menu_repo.get_all(self.session)
        else:
            user_roles = await self.role_repo.get_user_roles(user.id)
            menu_ids = set()
            all_menus = []
            for role in user_roles:
                role_menus = await self.role_repo.get_role_menus(role.id)
                for menu in role_menus:
                    if menu.id not in menu_ids and menu.menu_type in (0, 1):  # DIRECTORY或MENU
                        menu_ids.add(menu.id)
                        all_menus.append(menu)

        # 只保留DIRECTORY和MENU类型
        route_menus = [m for m in all_menus if m.menu_type in (0, 1)]

        # 构建树形路由
        return self._build_route_tree(route_menus)

    def _build_route_tree(self, menus: list, parent_id: str | None = None) -> list[dict]:
        """将扁平菜单列表构建为嵌套路由树。"""
        routes = []
        for menu in menus:
            if menu.parent_id == parent_id:
                route = {"path": menu.path, "name": menu.name, "rank": menu.rank, "component": menu.component, "meta": self._build_meta(menu)}
                children = self._build_route_tree(menus, menu.id)
                if children:
                    route["children"] = children
                routes.append(route)
        # 按rank排序
        return sorted(routes, key=lambda r: r.get("rank", 0))

    def _build_meta(self, menu) -> dict:
        """从Menu的关联MenuMeta构建meta对象。"""
        meta = menu.meta if hasattr(menu, "meta") and menu.meta else None
        if meta:
            return {
                "title": meta.title or "",
                "icon": meta.icon or "",
                "rSvgName": meta.r_svg_name or "",
                "showLink": bool(meta.is_show_menu),
                "showParent": bool(meta.is_show_parent),
                "keepAlive": bool(meta.is_keepalive),
                "frameUrl": meta.frame_url or "",
                "frameLoading": bool(meta.frame_loading),
                "transition": {"enter": meta.transition_enter or "", "leave": meta.transition_leave or ""} if meta.transition_enter or meta.transition_leave else {},
                "hiddenTag": bool(meta.is_hidden_tag),
                "fixedTag": bool(meta.fixed_tag),
                "dynamicLevel": meta.dynamic_level,
            }
        # 如果没有meta，返回基本meta
        return {"title": menu.name, "showLink": True, "keepAlive": False}
