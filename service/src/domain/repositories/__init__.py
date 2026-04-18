"""领域仓储接口模块。

此模块包含所有仓储的抽象接口定义。
仓储接口定义了数据持久化操作的契约，不依赖任何具体实现。
"""

from src.domain.repositories.department_repository import DepartmentRepositoryInterface
from src.domain.repositories.dictionary_repository import DictionaryRepositoryInterface
from src.domain.repositories.log_repository import LogRepositoryInterface
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.system_config_repository import SystemConfigRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface

__all__ = ["DepartmentRepositoryInterface", "DictionaryRepositoryInterface", "LogRepositoryInterface", "MenuRepositoryInterface", "RoleRepositoryInterface", "SystemConfigRepositoryInterface", "UserRepositoryInterface"]
