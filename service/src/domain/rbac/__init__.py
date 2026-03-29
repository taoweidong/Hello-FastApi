"""RBAC 领域包。"""

from src.domain.rbac.repository import PermissionRepositoryInterface, RoleRepositoryInterface
from src.infrastructure.database.models import Permission, Role, UserRole

__all__ = ["Permission", "PermissionRepositoryInterface", "Role", "RoleRepositoryInterface", "UserRole"]
