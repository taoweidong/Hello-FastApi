"""应用层 - 权限服务。"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.permission_dto import (
    PermissionCreateDTO,
    PermissionListQueryDTO,
    PermissionResponseDTO,
)
from src.core.exceptions import ConflictError, NotFoundError
from src.domain.repositories.permission_repository import PermissionRepositoryInterface
from src.infrastructure.database.models import Permission


class PermissionService:
    """权限操作的应用服务。"""

    def __init__(self, session: AsyncSession, perm_repo: PermissionRepositoryInterface):
        """初始化权限服务。

        Args:
            session: 数据库会话，用于事务控制
            perm_repo: 权限仓储接口实例
        """
        self.session = session
        self.perm_repo = perm_repo

    async def create_permission(self, dto: PermissionCreateDTO) -> PermissionResponseDTO:
        """创建新权限。"""
        # 检查权限编码是否已存在
        if await self.perm_repo.get_by_code(dto.code):
            raise ConflictError(f"权限编码 '{dto.code}' 已存在")

        permission = Permission(
            name=dto.name, code=dto.code, category=dto.category, description=dto.description, status=dto.status
        )
        permission = await self.perm_repo.create(permission)
        return self._perm_to_response(permission)

    async def get_permissions(self, query: PermissionListQueryDTO) -> tuple[list[PermissionResponseDTO], int]:
        """获取权限列表（分页）。"""
        # 获取总数
        total = await self.perm_repo.count(permission_name=query.permissionName)
        # 获取列表
        perms = await self.perm_repo.get_all(
            page_num=query.pageNum, page_size=query.pageSize, permission_name=query.permissionName
        )
        return [self._perm_to_response(p) for p in perms], total

    async def delete_permission(self, permission_id: str) -> bool:
        """删除权限。"""
        if not await self.perm_repo.delete(permission_id):
            raise NotFoundError(f"权限ID '{permission_id}' 不存在")
        return True

    async def get_user_permissions(self, user_id: str) -> list[PermissionResponseDTO]:
        """获取用户的所有权限（通过其角色）。"""
        perms = await self.perm_repo.get_user_permissions(user_id)
        return [self._perm_to_response(p) for p in perms]

    async def check_permission(self, user_id: str, codename: str) -> bool:
        """检查用户是否具有特定权限。"""
        perms = await self.perm_repo.get_user_permissions(user_id)
        return any(p.code == codename for p in perms)

    @staticmethod
    def _perm_to_response(perm: Permission) -> PermissionResponseDTO:
        """将Permission模型转换为响应DTO。"""
        return PermissionResponseDTO(
            id=perm.id,
            name=perm.name,
            code=perm.code,
            category=perm.category,
            description=perm.description,
            status=perm.status,
            createTime=perm.created_at,
        )
