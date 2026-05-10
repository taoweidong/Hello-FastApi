"""领域层模块。

领域层包含业务核心逻辑，遵循领域驱动设计（DDD）原则。
此模块不依赖任何外部层（infrastructure、config、api、application）。

子模块结构：
- entities/: 领域实体定义
- repositories/: 仓储接口定义
- services/: 领域服务
- exceptions.py: 应用与领域共享的异常类型
- rbac_defaults.py: RBAC 种子数据默认值
"""

# 导出实体
from src.domain.entities import (
    DepartmentEntity,
    LoginLogEntity,
    MenuEntity,
    MenuMetaEntity,
    OperationLogEntity,
    RoleEntity,
    SystemConfigEntity,
    UserEntity,
)

# 导出枚举
from src.domain.enums import Gender, LoginStatus, MenuType, PermissionMode, UserStatus, UserRole

# 导出仓储接口
from src.domain.repositories import (
    DepartmentRepositoryInterface,
    LogRepositoryInterface,
    MenuRepositoryInterface,
    RoleRepositoryInterface,
    SystemConfigRepositoryInterface,
    UserRepositoryInterface,
)

# 导出领域服务
from src.domain.services import PasswordService, TokenService

__all__ = [
    # 实体
    "UserEntity",
    "RoleEntity",
    "MenuEntity",
    "MenuMetaEntity",
    "DepartmentEntity",
    "SystemConfigEntity",
    "LoginLogEntity",
    "OperationLogEntity",
    # 仓储接口
    "UserRepositoryInterface",
    "RoleRepositoryInterface",
    "MenuRepositoryInterface",
    "DepartmentRepositoryInterface",
    "LogRepositoryInterface",
    "SystemConfigRepositoryInterface",
    # 领域服务
    "PasswordService",
    "TokenService",
    # 枚举
    "UserStatus",
    "UserRole",
    "Gender",
    "PermissionMode",
    "MenuType",
    "LoginStatus",
]
