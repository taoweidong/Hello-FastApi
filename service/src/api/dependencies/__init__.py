"""API 路由的依赖注入包。

统一导出所有认证依赖项和服务工厂函数，实现依赖倒置原则。
所有服务通过工厂函数创建，路由层通过 Depends() 注入。
"""

from src.api.dependencies.auth import get_current_active_user, get_current_user_id, require_menu_permission, require_permission, require_superuser, security_scheme
from src.api.dependencies.auth_service import get_auth_service
from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.department_service import get_department_service
from src.api.dependencies.dictionary_service import get_dictionary_service
from src.api.dependencies.domain_services import get_password_service, get_token_service
from src.api.dependencies.ip_rule_service import get_ip_rule_service
from src.api.dependencies.log_service import get_log_service
from src.api.dependencies.menu_service import get_menu_repository, get_menu_service
from src.api.dependencies.role_service import get_role_repository, get_role_service
from src.api.dependencies.system_config_service import get_system_config_service
from src.api.dependencies.user_service import get_user_repository, get_user_service

__all__ = [
    # 认证依赖
    "get_current_active_user",
    "get_current_user_id",
    "require_menu_permission",
    "require_permission",
    "require_superuser",
    "security_scheme",
    # 领域服务工厂
    "get_password_service",
    "get_token_service",
    # 应用服务工厂
    "get_auth_service",
    "get_department_service",
    "get_dictionary_service",
    "get_ip_rule_service",
    "get_log_service",
    "get_menu_service",
    "get_role_service",
    "get_system_config_service",
    "get_user_service",
    # 仓储工厂
    "get_menu_repository",
    "get_role_repository",
    "get_user_repository",
    # 缓存服务工厂
    "get_cache_service",
]
