"""数据库模型包 - 统一导出所有 ORM 模型类。

保持向后兼容：from src.infrastructure.database.models import User 仍然可用。
"""

from src.infrastructure.database.models.department import Department
from src.infrastructure.database.models.dictionary import Dictionary
from src.infrastructure.database.models.ip_rule import IPRule
from src.infrastructure.database.models.login_log import LoginLog
from src.infrastructure.database.models.menu import Menu
from src.infrastructure.database.models.menu_meta import MenuMeta
from src.infrastructure.database.models.role import Role
from src.infrastructure.database.models.role_menu_link import RoleMenuLink
from src.infrastructure.database.models.system_config import SystemConfig
from src.infrastructure.database.models.system_log import SystemLog
from src.infrastructure.database.models.user import User
from src.infrastructure.database.models.user_role import UserRole

__all__ = [
    "Department",
    "Dictionary",
    "IPRule",
    "LoginLog",
    "Menu",
    "MenuMeta",
    "Role",
    "RoleMenuLink",
    "SystemConfig",
    "SystemLog",
    "User",
    "UserRole",
]
