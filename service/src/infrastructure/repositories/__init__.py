"""仓储实现模块。

此模块包含所有仓储接口的具体实现，使用 FastCRUD 进行数据库操作。
"""

from src.infrastructure.repositories.department_repository import DepartmentRepository
from src.infrastructure.repositories.dictionary_repository import DictionaryRepository
from src.infrastructure.repositories.log_repository import LogRepository
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.system_config_repository import SystemConfigRepository
from src.infrastructure.repositories.user_repository import UserRepository

__all__ = ["DepartmentRepository", "DictionaryRepository", "LogRepository", "MenuRepository", "RoleRepository", "SystemConfigRepository", "UserRepository"]
