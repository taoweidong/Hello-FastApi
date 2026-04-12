"""RBAC 种子数据（角色与菜单默认值）。"""

# RBAC 默认角色
DEFAULT_ROLES = {"admin": "System administrator with full access", "user": "Regular user with basic access", "moderator": "Moderator with elevated permissions"}

# RBAC 默认菜单权限（新方案：使用Menu替代Permission）
# menu_type: 0=DIRECTORY, 1=MENU, 2=PERMISSION
# method: 用于PERMISSION类型菜单的HTTP方法
DEFAULT_MENUS = [
    # 系统管理目录
    {"name": "system", "path": "/system", "menu_type": 0, "rank": 1},
    # 用户管理页面
    {"name": "system:user", "path": "/system/user", "component": "system/user/index", "menu_type": 1, "rank": 1, "meta": {"title": "用户管理", "icon": "ri:user-line"}},
    # 用户管理按钮权限
    {"name": "system:user:view", "path": "/system/user", "menu_type": 2, "method": "GET"},
    {"name": "system:user:add", "path": "/system/user", "menu_type": 2, "method": "POST"},
    {"name": "system:user:edit", "path": "/system/user", "menu_type": 2, "method": "PUT"},
    {"name": "system:user:delete", "path": "/system/user", "menu_type": 2, "method": "DELETE"},
    # 角色管理页面
    {"name": "system:role", "path": "/system/role", "component": "system/role/index", "menu_type": 1, "rank": 2, "meta": {"title": "角色管理", "icon": "ri:admin-line"}},
    # 角色管理按钮权限
    {"name": "system:role:view", "path": "/system/role", "menu_type": 2, "method": "GET"},
    {"name": "system:role:add", "path": "/system/role", "menu_type": 2, "method": "POST"},
    {"name": "system:role:edit", "path": "/system/role", "menu_type": 2, "method": "PUT"},
    {"name": "system:role:delete", "path": "/system/role", "menu_type": 2, "method": "DELETE"},
    # 菜单管理页面
    {"name": "system:menu", "path": "/system/menu", "component": "system/menu/index", "menu_type": 1, "rank": 3, "meta": {"title": "菜单管理", "icon": "ri:menu-line"}},
    # 菜单管理按钮权限
    {"name": "system:menu:view", "path": "/system/menu", "menu_type": 2, "method": "GET"},
    {"name": "system:menu:add", "path": "/system/menu", "menu_type": 2, "method": "POST"},
    {"name": "system:menu:edit", "path": "/system/menu", "menu_type": 2, "method": "PUT"},
    {"name": "system:menu:delete", "path": "/system/menu", "menu_type": 2, "method": "DELETE"},
    # 部门管理页面
    {"name": "system:dept", "path": "/system/dept", "component": "system/dept/index", "menu_type": 1, "rank": 4, "meta": {"title": "部门管理", "icon": "ri:building-line"}},
    # 部门管理按钮权限
    {"name": "system:dept:view", "path": "/system/dept", "menu_type": 2, "method": "GET"},
    {"name": "system:dept:add", "path": "/system/dept", "menu_type": 2, "method": "POST"},
    {"name": "system:dept:edit", "path": "/system/dept", "menu_type": 2, "method": "PUT"},
    {"name": "system:dept:delete", "path": "/system/dept", "menu_type": 2, "method": "DELETE"},
    # 日志管理目录
    {"name": "system:log", "path": "/system/log", "menu_type": 0, "rank": 5},
    # 登录日志页面
    {"name": "system:login-log", "path": "/system/log/login", "component": "system/logs/login/index", "menu_type": 1, "rank": 1, "meta": {"title": "登录日志", "icon": "ri:file-list-line"}},
    # 操作日志页面
    {"name": "system:operation-log", "path": "/system/log/operation", "component": "system/logs/operation/index", "menu_type": 1, "rank": 2, "meta": {"title": "操作日志", "icon": "ri:file-code-line"}},
]

# admin角色默认拥有的菜单name列表（全部菜单）
ADMIN_MENU_NAMES = [m["name"] for m in DEFAULT_MENUS]

# user角色默认拥有的菜单name列表（只读权限）
USER_MENU_NAMES = ["system", "system:user", "system:user:view", "system:role", "system:role:view", "system:menu", "system:menu:view", "system:dept", "system:dept:view", "system:log", "system:login-log", "system:operation-log"]
