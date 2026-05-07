"""应用层 - 认证服务。"""

from datetime import datetime, timedelta, timezone

from src.application.dto.auth_dto import LoginDTO, RegisterDTO
from src.application.utils.menu_mapper import menu_dict_to_entity, menu_entity_to_dict
from src.config.settings import settings
from src.domain.entities.menu import MenuEntity
from src.domain.entities.user import UserEntity
from src.domain.exceptions import BusinessError, NotFoundError, UnauthorizedError
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.cache_port import CachePort
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService


class AuthService:
    """认证操作的应用服务。"""

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        role_repo: RoleRepositoryInterface,
        menu_repo: MenuRepositoryInterface,
        token_service: TokenService,
        password_service: PasswordService,
        cache_service: CachePort | None = None,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.menu_repo = menu_repo
        self.token_service = token_service
        self.password_service = password_service
        self.cache_service = cache_service

    async def login(self, dto: LoginDTO) -> dict:
        """认证用户并返回完整登录信息。"""
        # 1. 验证用户名密码
        user = await self.user_repo.get_by_username(dto.username)
        if user is None:
            raise UnauthorizedError("用户名或密码错误")

        if not self.password_service.verify_password(dto.password, user.password):
            raise UnauthorizedError("用户名或密码错误")

        # 2. 检查用户状态
        if not user.is_active_user:
            raise UnauthorizedError("用户账号已被禁用")

        # 3. 生成令牌
        token_data = {"sub": user.id, "username": user.username}
        access_token = self.token_service.create_access_token(token_data)
        refresh_token = self.token_service.create_refresh_token(token_data)

        # 4. 查询用户角色和菜单权限
        if user.is_superuser_user:
            user_roles = await self.role_repo.get_all(page_num=1, page_size=100)
            user_menus = await self._get_all_menus_cached()
        else:
            user_roles = await self.role_repo.get_user_roles(user.id)
            # 一次查询获取用户所有角色关联的菜单，消除 N+1
            user_menus = await self.role_repo.get_user_all_menus(user.id)

        # 5. 构建菜单名称列表（用于前端按钮权限 hasAuth 检查）
        menu_names = [m.name for m in user_menus if m.menu_type == MenuEntity.PERMISSION]

        # 6. 计算过期时间
        expires_time = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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

        user_entity = UserEntity.create_new(
            username=dto.username,
            hashed_password=hashed_password,
            nickname=dto.nickname,
            email=dto.email or "",
            phone=dto.phone or "",
        )
        created_user = await self.user_repo.create(user_entity)
        if created_user is None:
            raise NotFoundError("注册成功但无法加载用户")

        return {
            "id": created_user.id,
            "username": created_user.username,
            "nickname": created_user.nickname,
            "email": created_user.email,
            "phone": created_user.phone,
            "is_active": created_user.is_active,
        }

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
        if user is None or not user.is_active_user:
            raise UnauthorizedError("用户不存在或已被禁用")

        token_data = {"sub": user.id, "username": user.username}
        new_access_token = self.token_service.create_access_token(token_data)
        new_refresh_token = self.token_service.create_refresh_token(token_data)

        expires_time = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_str = expires_time.strftime("%Y/%m/%d %H:%M:%S")

        return {"accessToken": new_access_token, "refreshToken": new_refresh_token, "expires": expires_str}

    async def logout(self, access_token: str) -> bool:
        """登出：将 access_token 写入黑名单。"""
        if self.cache_service is None:
            return True
        payload = self.token_service.decode_token(access_token)
        if payload is None:
            return True
        exp = payload.get("exp")
        if exp is None:
            return True
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        return await self.cache_service.add_token_to_blacklist(access_token, expires_at)

    async def get_async_routes(self, user_id: str) -> list[dict]:
        """根据用户角色获取动态路由（从数据库Menu+MenuMeta构建）。"""
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            return []

        # 获取用户的菜单（仅DIRECTORY和MENU类型）
        if user.is_superuser_user:
            all_menus = await self._get_all_menus_cached()
        else:
            # 一次查询获取用户所有角色关联的菜单，消除 N+1
            all_menus = await self.role_repo.get_user_all_menus(user.id)

        # 只保留DIRECTORY和MENU类型
        route_menus = [m for m in all_menus if m.menu_type in (MenuEntity.DIRECTORY, MenuEntity.MENU_PAGE)]

        # 构建树形路由
        return self._build_route_tree(route_menus)

    async def _get_all_menus_cached(self) -> list[MenuEntity]:
        """获取所有菜单（带缓存），用于超级用户场景。"""
        if self.cache_service is not None:
            cached = await self.cache_service.get_all_menus()
            if cached is not None:
                return [self._menu_dict_to_entity(m) for m in cached]

        menus = await self.menu_repo.get_all()

        if self.cache_service is not None:
            await self.cache_service.set_all_menus([self._menu_entity_to_dict(m) for m in menus])

        return menus

    @staticmethod
    def _menu_entity_to_dict(menu: MenuEntity) -> dict:
        """将菜单实体转为可序列化的字典。"""
        return menu_entity_to_dict(menu)

    @staticmethod
    def _menu_dict_to_entity(data: dict) -> MenuEntity:
        """将序列化的字典转回菜单实体。"""
        return menu_dict_to_entity(data)

    def _build_route_tree(self, menus: list, parent_id: str | None = None) -> list[dict]:
        """将扁平菜单列表构建为嵌套路由树。"""
        routes = []
        for menu in menus:
            if menu.parent_id == parent_id:
                route = {
                    "path": menu.path,
                    "name": menu.name,
                    "rank": menu.rank,
                    "component": menu.component,
                    "meta": self._build_meta(menu),
                }
                children = self._build_route_tree(menus, menu.id)
                if children:
                    route["children"] = children
                routes.append(route)
        # 按rank排序
        return sorted(routes, key=lambda r: r.get("rank", 0))

    def _build_meta(self, menu: MenuEntity) -> dict:
        """从菜单实体的meta字段构建meta对象。"""
        meta = menu.meta
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
                "transition": {"enter": meta.transition_enter or "", "leave": meta.transition_leave or ""}
                if meta.transition_enter or meta.transition_leave
                else {},
                "hiddenTag": bool(meta.is_hidden_tag),
                "fixedTag": bool(meta.fixed_tag),
                "dynamicLevel": meta.dynamic_level,
            }
        # 如果没有meta，返回基本meta
        return {"title": menu.name, "showLink": True, "keepAlive": False}

    async def get_user_role_ids(self, user_id: str) -> list[str]:
        """根据用户ID获取对应角色ID列表。"""
        roles = await self.role_repo.get_user_roles(user_id)
        return [r.id for r in roles]

    async def get_role_menu_ids(self, role_id: str) -> list[str]:
        """根据角色ID获取菜单ID列表（admin角色返回全部）。"""
        role = await self.role_repo.get_by_id(role_id)
        if role and role.code == "admin":
            all_menus = await self.menu_repo.get_all()
            return [m.id for m in all_menus]
        return await self.role_repo.get_role_menu_ids(role_id)
