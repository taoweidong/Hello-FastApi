"""领域实体模块。

此模块包含所有领域实体的定义，使用 Python dataclass 实现。
领域实体是纯粹的数据载体，不依赖任何外部库（如 ORM）。
"""

from src.domain.entities.department import DepartmentEntity
from src.domain.entities.dictionary import DictionaryEntity
from src.domain.entities.ip_rule import IPRuleEntity
from src.domain.entities.log import LoginLogEntity, OperationLogEntity, SystemLogEntity
from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.system_config import SystemConfigEntity
from src.domain.entities.user import UserEntity

__all__ = ["DepartmentEntity", "DictionaryEntity", "IPRuleEntity", "LoginLogEntity", "MenuEntity", "MenuMetaEntity", "OperationLogEntity", "RoleEntity", "SystemConfigEntity", "SystemLogEntity", "UserEntity"]
