"""RBAC 种子数据（角色与菜单默认值）。"""

# RBAC 默认角色
DEFAULT_ROLES = {"admin": "系统管理员，拥有所有权限", "user": "普通用户，拥有基本只读权限", "moderator": "版主，拥有部分管理权限"}

# RBAC 默认菜单权限
# menu_type: 0=DIRECTORY, 1=MENU, 2=PERMISSION
# method: 用于PERMISSION类型菜单的HTTP方法
# parent_id: 引用同列表中已定义条目的name字段
DEFAULT_MENUS = [
    # === 系统管理目录 ===
    {"name": "System", "path": "/system", "menu_type": 0, "rank": 1, "meta": {"title": "系统管理", "icon": "ri:settings-3-line"}},
    # --- 用户管理 ---
    {"name": "User", "path": "/system/user", "component": "system/user/index", "menu_type": 1, "rank": 1, "parent_id": "System", "meta": {"title": "用户管理", "icon": "ri:admin-line"}, "description": "管理系统用户账号，支持新增、编辑、删除及角色分配"},
    {"name": "user:view", "path": "/system/user", "menu_type": 2, "method": "GET", "parent_id": "User"},
    {"name": "user:add", "path": "/system/user", "menu_type": 2, "method": "POST", "parent_id": "User"},
    {"name": "user:edit", "path": "/system/user", "menu_type": 2, "method": "PUT", "parent_id": "User"},
    {"name": "user:delete", "path": "/system/user", "menu_type": 2, "method": "DELETE", "parent_id": "User"},
    # --- 角色管理 ---
    {"name": "Role", "path": "/system/role", "component": "system/role/index", "menu_type": 1, "rank": 2, "parent_id": "System", "meta": {"title": "角色管理", "icon": "ri:admin-fill"}, "description": "管理系统角色定义及菜单权限分配"},
    {"name": "role:view", "path": "/system/role", "menu_type": 2, "method": "GET", "parent_id": "Role"},
    {"name": "role:manage", "path": "/system/role", "menu_type": 2, "method": "POST", "parent_id": "Role"},
    # --- 菜单管理 ---
    {"name": "Menu", "path": "/system/menu", "component": "system/menu/index", "menu_type": 1, "rank": 3, "parent_id": "System", "meta": {"title": "菜单管理", "icon": "ep:menu"}, "description": "管理系统导航菜单及路由配置"},
    {"name": "menu:view", "path": "/system/menu", "menu_type": 2, "method": "GET", "parent_id": "Menu"},
    {"name": "menu:add", "path": "/system/menu", "menu_type": 2, "method": "POST", "parent_id": "Menu"},
    {"name": "menu:edit", "path": "/system/menu", "menu_type": 2, "method": "PUT", "parent_id": "Menu"},
    {"name": "menu:delete", "path": "/system/menu", "menu_type": 2, "method": "DELETE", "parent_id": "Menu"},
    # --- 部门管理 ---
    {"name": "Dept", "path": "/system/dept", "component": "system/dept/index", "menu_type": 1, "rank": 4, "parent_id": "System", "meta": {"title": "部门管理", "icon": "ri:git-branch-line"}, "description": "管理组织架构部门层级及人员归属"},
    {"name": "dept:view", "path": "/system/dept", "menu_type": 2, "method": "GET", "parent_id": "Dept"},
    {"name": "dept:add", "path": "/system/dept", "menu_type": 2, "method": "POST", "parent_id": "Dept"},
    {"name": "dept:edit", "path": "/system/dept", "menu_type": 2, "method": "PUT", "parent_id": "Dept"},
    {"name": "dept:delete", "path": "/system/dept", "menu_type": 2, "method": "DELETE", "parent_id": "Dept"},
    # --- 字典管理 ---
    {"name": "Dictionary", "path": "/system/dictionary", "component": "system/dictionary/index", "menu_type": 1, "rank": 5, "parent_id": "System", "meta": {"title": "字典管理", "icon": "ri:book-read-line"}, "description": "管理系统业务字典数据，支持树形层级结构"},
    {"name": "dictionary:view", "path": "/system/dictionary", "menu_type": 2, "method": "GET", "parent_id": "Dictionary"},
    {"name": "dictionary:add", "path": "/system/dictionary", "menu_type": 2, "method": "POST", "parent_id": "Dictionary"},
    {"name": "dictionary:edit", "path": "/system/dictionary", "menu_type": 2, "method": "PUT", "parent_id": "Dictionary"},
    {"name": "dictionary:delete", "path": "/system/dictionary", "menu_type": 2, "method": "DELETE", "parent_id": "Dictionary"},
    # --- IP规则 ---
    {"name": "IpRule", "path": "/system/ip-rule", "component": "system/ip-rule/index", "menu_type": 1, "rank": 5, "parent_id": "System", "meta": {"title": "IP规则", "icon": "ri:shield-keyhole-line"}, "description": "配置 IP 白名单或黑名单访问控制规则"},
    {"name": "ip-rule:view", "path": "/system/ip-rule", "menu_type": 2, "method": "GET", "parent_id": "IpRule"},
    {"name": "ip-rule:add", "path": "/system/ip-rule", "menu_type": 2, "method": "POST", "parent_id": "IpRule"},
    {"name": "ip-rule:edit", "path": "/system/ip-rule", "menu_type": 2, "method": "PUT", "parent_id": "IpRule"},
    {"name": "ip-rule:delete", "path": "/system/ip-rule", "menu_type": 2, "method": "DELETE", "parent_id": "IpRule"},
    # --- 系统配置 ---
    {"name": "SystemConfig", "path": "/system/config", "component": "system/config/index", "menu_type": 1, "rank": 6, "parent_id": "System", "meta": {"title": "系统配置", "icon": "ri:settings-4-line"}, "description": "管理系统全局参数及运行配置"},
    {"name": "config:view", "path": "/system/config", "menu_type": 2, "method": "GET", "parent_id": "SystemConfig"},
    {"name": "config:add", "path": "/system/config", "menu_type": 2, "method": "POST", "parent_id": "SystemConfig"},
    {"name": "config:edit", "path": "/system/config", "menu_type": 2, "method": "PUT", "parent_id": "SystemConfig"},
    {"name": "config:delete", "path": "/system/config", "menu_type": 2, "method": "DELETE", "parent_id": "SystemConfig"},
    # --- 日志管理 ---
    {"name": "Log", "path": "/system/log", "menu_type": 0, "rank": 7, "parent_id": "System", "meta": {"title": "日志管理", "icon": "ri:file-list-line"}},
    {"name": "LoginLog", "path": "/system/log/login", "component": "system/logs/login/index", "menu_type": 1, "rank": 1, "parent_id": "Log", "meta": {"title": "登录日志", "icon": "ri:window-line"}, "description": "查询用户登录历史记录及登录状态统计"},
    {"name": "OperationLog", "path": "/system/log/operation", "component": "system/logs/operation/index", "menu_type": 1, "rank": 2, "parent_id": "Log", "meta": {"title": "操作日志", "icon": "ri:history-fill"}, "description": "查询用户操作行为日志及接口调用记录"},
    {"name": "log:view", "path": "/system/log", "menu_type": 2, "method": "GET", "parent_id": "Log"},
    {"name": "log:delete", "path": "/system/log", "menu_type": 2, "method": "DELETE", "parent_id": "Log"},
    # === 系统监控目录 ===
    {"name": "Monitor", "path": "/monitor", "menu_type": 0, "rank": 2, "meta": {"title": "系统监控", "icon": "ep:monitor"}},
    {"name": "OnlineUser", "path": "/monitor/online-user", "component": "monitor/online/index", "menu_type": 1, "rank": 1, "parent_id": "Monitor", "meta": {"title": "在线用户", "icon": "ri:user-voice-line"}, "description": "查看当前在线用户列表，支持强制下线操作"},
    {"name": "monitor:view", "path": "/monitor", "menu_type": 2, "method": "GET", "parent_id": "Monitor"},
    {"name": "monitor:manage", "path": "/monitor", "menu_type": 2, "method": "POST", "parent_id": "Monitor"},
]

# admin角色默认拥有的菜单name列表（全部菜单）
ADMIN_MENU_NAMES = [m["name"] for m in DEFAULT_MENUS]

# user角色默认拥有的菜单name列表（只读权限）
USER_MENU_NAMES = [
    "System", "User", "user:view",
    "Role", "role:view",
    "Menu", "menu:view",
    "Dept", "dept:view",
    "Dictionary", "dictionary:view",
    "IpRule", "ip-rule:view",
    "SystemConfig", "config:view",
    "Log", "LoginLog", "OperationLog", "log:view",
    "Monitor", "OnlineUser", "monitor:view",
]
