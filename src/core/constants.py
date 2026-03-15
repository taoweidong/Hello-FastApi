"""应用程序常量。"""

# API
API_PREFIX = "/api"
API_V1_PREFIX = "/api/v1"

# 分页
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# RBAC 默认角色
DEFAULT_ROLES = {
    "admin": "System administrator with full access",
    "user": "Regular user with basic access",
    "moderator": "Moderator with elevated permissions",
}

# RBAC 默认权限
DEFAULT_PERMISSIONS = [
    {"name": "View Users", "codename": "user.view", "resource": "user", "action": "view"},
    {"name": "Create Users", "codename": "user.create", "resource": "user", "action": "create"},
    {"name": "Update Users", "codename": "user.update", "resource": "user", "action": "update"},
    {"name": "Delete Users", "codename": "user.delete", "resource": "user", "action": "delete"},
    {"name": "View Roles", "codename": "role.view", "resource": "role", "action": "view"},
    {"name": "Manage Roles", "codename": "role.manage", "resource": "role", "action": "manage"},
    {"name": "View Permissions", "codename": "permission.view", "resource": "permission", "action": "view"},
    {"name": "Manage Permissions", "codename": "permission.manage", "resource": "permission", "action": "manage"},
]
