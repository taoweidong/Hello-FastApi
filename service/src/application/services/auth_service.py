"""应用层 - 认证服务。"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from loguru import logger

from src.application.dto.auth_dto import LoginDTO, RegisterDTO
from src.application.utils.menu_mapper import menu_dict_to_entity, menu_entity_to_dict
from src.application.utils.user_agent import extract_user_agent_info
from src.config.settings import settings
from src.domain.entities.log import LoginLogEntity
from src.domain.entities.menu import MenuEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import MenuType, SystemRole
from src.domain.error_messages import ErrorMessages as EM
from src.domain.exceptions import BusinessError, NotFoundError, UnauthorizedError
from src.domain.repositories.log_repository import LogRepositoryInterface
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.cache_port import CachePort
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService


@dataclass
class LoginRequestInfo:
    """登录请求的多源信息（IP/User-Agent）。

    由 API 层从 Request 对象提取后传入，供登录日志与在线会话登记使用。
    """

    client_ip: str | None = None
    user_agent: str | None = None


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
        log_repo: LogRepositoryInterface | None = None,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.menu_repo = menu_repo
        self.token_service = token_service
        self.password_service = password_service
        self.cache_service = cache_service
        self.log_repo = log_repo

    async def login(self, dto: LoginDTO, request_info: LoginRequestInfo | None = None) -> dict:
        """认证用户并返回完整登录信息。

        Args:
            dto: 登录 DTO
            request_info: 请求信息（IP/User-Agent），用于写登录日志与登记在线会话

        Returns:
            登录响应字典

        Raises:
            UnauthorizedError: 用户名密码错误或用户被禁用
        """
        try:
            user = await self._authenticate_user(dto)
        except UnauthorizedError:
            # 认证失败：记录失败日志后继续抛出（日志写入内部降级，不阻断请求）
            await self._write_login_log(username=dto.username, status=0, request_info=request_info)
            raise

        tokens = self._generate_tokens(user)
        roles, permissions = await self._get_user_roles_and_permissions(user)
        # 写登录日志与登记在线会话（均内部降级，不影响登录主流程）
        await self._write_login_log(
            username=user.username, status=1, request_info=request_info, creator_id=user.id, description="登录成功"
        )
        await self._register_online_session(user=user, access_token=tokens["access_token"], request_info=request_info)
        return self._build_login_response(user, tokens, roles, permissions)

    async def get_mine_logs(
        self, username: str, page_num: int = 1, page_size: int = 10
    ) -> tuple[list[LoginLogEntity], int]:
        """获取当前用户的安全日志（按登录用户名过滤）。

        返回最近登录/认证失败记录（含成功与失败），供账户设置-个人安全日志展示。
        日志仓储缺失或查询异常时降级返回空列表，不阻断请求。
        """
        if self.log_repo is None:
            return [], 0
        try:
            return await self.log_repo.get_login_logs(page_num=page_num, page_size=page_size, username=username)
        except Exception:
            logger.warning(f"获取个人安全日志失败：username={username}", exc_info=True)
            return [], 0

    async def _write_login_log(
        self,
        username: str,
        status: int,
        request_info: LoginRequestInfo | None,
        creator_id: str | None = None,
        description: str | None = None,
    ) -> None:
        """写入登录日志。

        写库失败仅记录告警，不阻断登录流程（降级安全）。
        """
        if self.log_repo is None:
            return
        try:
            if request_info is not None:
                browser, system = extract_user_agent_info(request_info.user_agent or "")
                client_ip = request_info.client_ip
                agent = request_info.user_agent
            else:
                browser, system = "unknown", "unknown"
                client_ip = None
                agent = None
            entity = LoginLogEntity.create_new(
                status=status,
                username=username,
                ipaddress=client_ip,
                browser=browser,
                system=system,
                agent=agent,
                login_type=0,  # 0-密码登录
                description=description,
            )
            entity.creator_id = creator_id
            await self.log_repo.create_login_log(entity)
        except Exception:
            logger.warning(f"写入登录日志失败：username={username}", exc_info=True)

    async def _register_online_session(
        self, user: UserEntity, access_token: str, request_info: LoginRequestInfo | None
    ) -> None:
        """登记在线用户会话（Redis）。

        会话 Key 与 Token 黑名单共用同一哈希前缀，便于强制下线直接拉黑；
        Redis 不可用时静默降级，不影响登录主流程。
        """
        if self.cache_service is None:
            return
        try:
            if request_info is not None:
                browser, system = extract_user_agent_info(request_info.user_agent or "")
                client_ip = request_info.client_ip
            else:
                browser, system = "unknown", "unknown"
                client_ip = None
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            info = {
                "userId": user.id,
                "username": user.username,
                "ip": client_ip,
                "system": system,
                "browser": browser,
                "loginTime": datetime.now(timezone.utc).isoformat(),
                "expiresAt": expires_at.isoformat(),
            }
            session_key = self.token_service.hash_token(access_token)
            await self.cache_service.set_online_user(session_key, info, expires_at)
        except Exception:
            logger.warning(f"登记在线用户会话失败：username={user.username}", exc_info=True)

    async def _authenticate_user(self, dto: LoginDTO) -> UserEntity:
        """验证用户名密码和用户状态。

        Args:
            dto: 登录 DTO

        Returns:
            验证通过的用户实体

        Raises:
            UnauthorizedError: 用户名密码错误或用户被禁用
        """
        user = await self.user_repo.get_by_username(dto.username)
        if user is None:
            raise UnauthorizedError(EM.INVALID_USERNAME_OR_PASSWORD)

        if not self.password_service.verify_password(dto.password, user.password):
            raise UnauthorizedError(EM.INVALID_USERNAME_OR_PASSWORD)

        if not user.is_active_user:
            raise UnauthorizedError(EM.USER_ACCOUNT_DISABLED)

        return user

    def _generate_tokens(self, user: UserEntity) -> dict[str, str]:
        """生成访问令牌和刷新令牌。

        Args:
            user: 用户实体

        Returns:
            包含 access_token 和 refresh_token 的字典
        """
        token_data = {"sub": user.id, "username": user.username}
        return {
            "access_token": self.token_service.create_access_token(token_data),
            "refresh_token": self.token_service.create_refresh_token(token_data),
        }

    async def _get_user_roles_and_permissions(self, user: UserEntity) -> tuple[list[str], list[str]]:
        """获取用户角色和权限列表。

        Args:
            user: 用户实体

        Returns:
            (角色列表, 权限列表) 元组
        """
        if user.is_superuser_user:
            user_roles = await self.role_repo.get_all(page_num=1, page_size=100)
            user_menus = await self._get_all_menus_cached()
        else:
            user_roles = await self.role_repo.get_user_roles(user.id)
            user_menus = await self.role_repo.get_user_all_menus(user.id)

        role_names = [role.name for role in user_roles]
        menu_names = [m.name for m in user_menus if m.menu_type == MenuType.PERMISSION]

        return role_names, menu_names

    def _build_login_response(
        self, user: UserEntity, tokens: dict[str, str], roles: list[str], permissions: list[str]
    ) -> dict:
        """构建登录响应数据。

        Args:
            user: 用户实体
            tokens: 令牌字典
            roles: 角色列表
            permissions: 权限列表

        Returns:
            登录响应字典
        """
        expires_time = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_str = expires_time.strftime("%Y/%m/%d %H:%M:%S")

        return {
            "avatar": user.avatar or "",
            "username": user.username,
            "nickname": user.nickname or user.username,
            "roles": roles,
            "permissions": permissions,
            "accessToken": tokens["access_token"],
            "refreshToken": tokens["refresh_token"],
            "expires": expires_str,
        }

    async def register(self, dto: RegisterDTO) -> dict:
        """用户注册。"""
        existing_user = await self.user_repo.get_by_username(dto.username)
        if existing_user is not None:
            raise BusinessError(EM.USERNAME_EXISTS)

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
            raise NotFoundError(EM.REGISTER_LOAD_FAILED)

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
            raise UnauthorizedError(EM.INVALID_REFRESH_TOKEN)

        if not self.token_service.verify_token_type(payload, "refresh"):
            raise UnauthorizedError(EM.INVALID_TOKEN_TYPE)

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError(EM.INVALID_REFRESH_TOKEN)

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active_user:
            raise UnauthorizedError(EM.USER_NOT_FOUND_OR_DISABLED)

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
        route_menus = [m for m in all_menus if m.menu_type in (MenuType.DIRECTORY, MenuType.MENU)]

        # 汇总各菜单下的按钮权限码（PERMISSION类型子节点），供前端 hasAuth 判断
        auths_map: dict[str, list[str]] = {}
        for menu in all_menus:
            if menu.menu_type == MenuType.PERMISSION and menu.parent_id:
                auths_map.setdefault(menu.parent_id, []).append(menu.name)

        # 构建树形路由
        return self._build_route_tree(route_menus, auths_map=auths_map)

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

    def _build_route_tree(
        self, menus: list, parent_id: str | None = None, auths_map: dict[str, list[str]] | None = None
    ) -> list[dict]:
        """将扁平菜单列表构建为嵌套路由树。"""
        routes = []
        for menu in menus:
            if menu.parent_id == parent_id:
                meta = self._build_meta(menu)
                # 挂载当前菜单的按钮权限码列表，前端通过 meta.auths 做按钮级控制
                menu_auths = (auths_map or {}).get(menu.id, [])
                if menu_auths:
                    meta["auths"] = menu_auths
                route = {
                    "path": menu.path,
                    "name": menu.name,
                    "rank": menu.rank,
                    "component": menu.component,
                    "meta": meta,
                }
                children = self._build_route_tree(menus, menu.id, auths_map)
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
        if role and role.code == SystemRole.ADMIN:
            all_menus = await self.menu_repo.get_all()
            return [m.id for m in all_menus]
        return await self.role_repo.get_role_menu_ids(role_id)
