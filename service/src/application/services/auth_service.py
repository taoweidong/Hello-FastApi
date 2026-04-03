"""应用层 - 认证服务。"""

from datetime import datetime, timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.auth_dto import LoginDTO, RegisterDTO
from src.config.settings import settings
from src.core.exceptions import BusinessError, UnauthorizedError
from src.domain.repositories.permission_repository import PermissionRepositoryInterface
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService
from src.infrastructure.database.models import User


class AuthService:
    """认证操作的应用服务。"""

    def __init__(self, session: AsyncSession, user_repo: UserRepositoryInterface, role_repo: RoleRepositoryInterface, perm_repo: PermissionRepositoryInterface, token_service: TokenService, password_service: PasswordService):
        """初始化认证服务。

        Args:
            session: 数据库会话，用于事务控制
            user_repo: 用户仓储接口实例
            role_repo: 角色仓储接口实例
            perm_repo: 权限仓储接口实例
            token_service: 令牌服务实例
            password_service: 密码服务实例
        """
        self.session = session
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.perm_repo = perm_repo
        self.token_service = token_service
        self.password_service = password_service

    async def login(self, dto: LoginDTO) -> dict:
        """认证用户并返回完整登录信息。

        Args:
            dto: 登录请求数据

        Returns:
            dict: 包含 accessToken, expires, refreshToken, userInfo, roles, permissions 的完整登录响应

        Raises:
            UnauthorizedError: 用户名密码错误或用户被禁用
        """
        # 1. 验证用户名密码
        user = await self.user_repo.get_by_username(dto.username)
        if user is None:
            raise UnauthorizedError("用户名或密码错误")

        if not self.password_service.verify_password(dto.password, user.hashed_password):
            raise UnauthorizedError("用户名或密码错误")

        # 2. 检查用户状态（status=1 表示启用）
        if user.status != 1:
            raise UnauthorizedError("用户账号已被禁用")

        # 3. 生成令牌
        token_data = {"sub": user.id, "username": user.username}
        access_token = self.token_service.create_access_token(token_data)
        refresh_token = self.token_service.create_refresh_token(token_data)

        # 4. 查询用户角色和权限
        # 超级管理员直接返回 admin 角色和所有权限
        if user.is_superuser:
            user_roles = await self.role_repo.get_all(page_num=1, page_size=100)
            user_permissions = await self.perm_repo.get_all(page_num=1, page_size=100)
        else:
            user_roles = await self.role_repo.get_user_roles(user.id)
            user_permissions = await self.perm_repo.get_user_permissions(user.id)

        # 5. 计算过期时间为日期字符串格式
        expires_time = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_str = expires_time.strftime("%Y/%m/%d %H:%M:%S")

        # 6. 构建扁平结构的登录响应（与 Pure Admin 前端 Mock 一致）
        return {"avatar": user.avatar or "", "username": user.username, "nickname": user.nickname or user.username, "roles": [role.name for role in user_roles], "permissions": [perm.code for perm in user_permissions], "accessToken": access_token, "refreshToken": refresh_token, "expires": expires_str}

    async def register(self, dto: RegisterDTO) -> dict:
        """用户注册。

        Args:
            dto: 注册请求数据

        Returns:
            dict: 包含新创建用户基本信息的响应

        Raises:
            BusinessError: 用户名已存在
        """
        # 1. 检查用户名唯一性
        existing_user = await self.user_repo.get_by_username(dto.username)
        if existing_user is not None:
            raise BusinessError("用户名已存在")

        # 2. 密码哈希
        hashed_password = self.password_service.hash_password(dto.password)

        # 3. 创建用户（status=1 表示启用）
        new_user = User(username=dto.username, hashed_password=hashed_password, nickname=dto.nickname, email=dto.email or "", phone=dto.phone, status=1)
        created_user = await self.user_repo.create(new_user)
        await self.session.commit()

        # 4. 返回用户基本信息
        return {"id": created_user.id, "username": created_user.username, "nickname": created_user.nickname, "email": created_user.email, "phone": created_user.phone, "status": created_user.status}

    async def refresh_token(self, refresh_token: str) -> dict:
        """使用刷新令牌刷新访问令牌。

        Args:
            refresh_token: 刷新令牌字符串

        Returns:
            dict: 包含 accessToken, expires, refreshToken 的响应

        Raises:
            UnauthorizedError: 令牌无效或用户不存在/被禁用
        """
        payload = self.token_service.decode_token(refresh_token)
        if payload is None:
            raise UnauthorizedError("无效的刷新令牌")

        if not self.token_service.verify_token_type(payload, "refresh"):
            raise UnauthorizedError("无效的令牌类型")

        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("无效的刷新令牌")

        user = await self.user_repo.get_by_id(user_id)
        if user is None or user.status != 1:
            raise UnauthorizedError("用户不存在或已被禁用")

        token_data = {"sub": user.id, "username": user.username}
        new_access_token = self.token_service.create_access_token(token_data)
        new_refresh_token = self.token_service.create_refresh_token(token_data)

        # 计算过期时间为日期字符串格式
        expires_time = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_str = expires_time.strftime("%Y/%m/%d %H:%M:%S")

        return {"accessToken": new_access_token, "refreshToken": new_refresh_token, "expires": expires_str}
