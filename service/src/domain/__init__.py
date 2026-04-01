"""领域层模块。

领域层包含业务核心逻辑，遵循领域驱动设计（DDD）原则。
此模块不依赖任何外部层（infrastructure、config、api、application）。

子模块结构：
- entities/: 领域实体定义
- repositories/: 仓储接口定义
- services/: 领域服务
"""

# 导出实体
from src.domain.entities import DepartmentEntity, LoginLogEntity, MenuEntity, OperationLogEntity, PermissionEntity, RoleEntity, SystemLogEntity, UserEntity

# 导出仓储接口
from src.domain.repositories import DepartmentRepositoryInterface, LogRepositoryInterface, MenuRepositoryInterface, PermissionRepositoryInterface, RoleRepositoryInterface, UserRepositoryInterface

# 导出领域服务
from src.domain.services import PasswordService, TokenService

__all__ = [
    # 实体
    "UserEntity",
    "RoleEntity",
    "PermissionEntity",
    "MenuEntity",
    "DepartmentEntity",
    "LoginLogEntity",
    "OperationLogEntity",
    "SystemLogEntity",
    # 仓储接口
    "UserRepositoryInterface",
    "RoleRepositoryInterface",
    "PermissionRepositoryInterface",
    "MenuRepositoryInterface",
    "DepartmentRepositoryInterface",
    "LogRepositoryInterface",
    # 领域服务
    "PasswordService",
    "TokenService",
]
