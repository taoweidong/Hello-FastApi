"""应用程序常量。"""

# API
API_PREFIX = "/api"
API_SYSTEM_PREFIX = "/api/system"

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
    # 用户相关权限
    {"name": "查看用户", "code": "user:view", "resource": "user", "action": "view"},
    {"name": "创建用户", "code": "user:add", "resource": "user", "action": "add"},
    {"name": "编辑用户", "code": "user:edit", "resource": "user", "action": "edit"},
    {"name": "删除用户", "code": "user:delete", "resource": "user", "action": "delete"},
    # 角色相关权限
    {"name": "查看角色", "code": "role:view", "resource": "role", "action": "view"},
    {"name": "管理角色", "code": "role:manage", "resource": "role", "action": "manage"},
    # 权限相关权限
    {"name": "查看权限", "code": "permission:view", "resource": "permission", "action": "view"},
    {"name": "管理权限", "code": "permission:manage", "resource": "permission", "action": "manage"},
    # 菜单相关权限
    {"name": "查看菜单", "code": "menu:view", "resource": "menu", "action": "view"},
    {"name": "创建菜单", "code": "menu:add", "resource": "menu", "action": "add"},
    {"name": "编辑菜单", "code": "menu:edit", "resource": "menu", "action": "edit"},
    {"name": "删除菜单", "code": "menu:delete", "resource": "menu", "action": "delete"},
    # 部门相关权限
    {"name": "查看部门", "code": "dept:view", "resource": "dept", "action": "view"},
    {"name": "创建部门", "code": "dept:add", "resource": "dept", "action": "add"},
    {"name": "编辑部门", "code": "dept:edit", "resource": "dept", "action": "edit"},
    {"name": "删除部门", "code": "dept:delete", "resource": "dept", "action": "delete"},
    # 日志相关权限
    {"name": "查看登录日志", "code": "login-log:view", "resource": "login-log", "action": "view"},
    {"name": "删除登录日志", "code": "login-log:delete", "resource": "login-log", "action": "delete"},
    {"name": "查看操作日志", "code": "operation-log:view", "resource": "operation-log", "action": "view"},
    {"name": "删除操作日志", "code": "operation-log:delete", "resource": "operation-log", "action": "delete"},
    {"name": "查看系统日志", "code": "system-log:view", "resource": "system-log", "action": "view"},
    {"name": "删除系统日志", "code": "system-log:delete", "resource": "system-log", "action": "delete"},
]
