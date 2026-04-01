"""领域实体模块。

此模块包含所有领域实体的定义，使用 Python dataclass 实现。
领域实体是纯粹的数据载体，不依赖任何外部库（如 ORM）。
"""

from src.domain.entities.department import DepartmentEntity
from src.domain.entities.log import LoginLogEntity, OperationLogEntity, SystemLogEntity
from src.domain.entities.menu import MenuEntity
from src.domain.entities.permission import PermissionEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity

__all__ = ["UserEntity", "RoleEntity", "PermissionEntity", "MenuEntity", "DepartmentEntity", "LoginLogEntity", "OperationLogEntity", "SystemLogEntity"]
