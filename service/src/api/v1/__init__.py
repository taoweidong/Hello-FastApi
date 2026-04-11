"""System API package - 路由聚合模块。

该模块负责聚合所有系统级别的 API 路由，使用 classy-fastapi 类设计。
"""

from fastapi import APIRouter

from src.api.v1.auth_router import AuthRouter
from src.api.v1.dept_router import DeptRouter
from src.api.v1.log_router import LogRouter
from src.api.v1.menu_router import MenuRouter
from src.api.v1.monitor_router import MonitorRouter
from src.api.v1.permission_router import PermissionRouter
from src.api.v1.role_router import RoleRouter
from src.api.v1.user_router import UserRouter

# 创建系统级路由聚合器
system_router = APIRouter()

# 认证路由直接挂在 system 路由下（无额外前缀）
# 提供登录、注册、登出、刷新令牌等接口
system_router.include_router(AuthRouter().router, tags=["认证管理"])

# 用户管理路由
# 前缀: /user
# 提供用户增删改查、密码管理等功能
system_router.include_router(UserRouter().router, prefix="/user", tags=["用户管理"])

# 角色管理路由
# 前缀: /role
# 提供角色增删改查、权限分配等功能
system_router.include_router(RoleRouter().router, prefix="/role", tags=["角色管理"])

# 权限管理路由
# 前缀: /permission
# 提供权限增删改查等功能
system_router.include_router(PermissionRouter().router, prefix="/permission", tags=["权限管理"])

# 菜单管理路由
# 前缀: /menu
# 提供菜单增删改查、菜单树获取等功能
system_router.include_router(MenuRouter().router, prefix="/menu", tags=["菜单管理"])

# 部门管理路由
# 直接挂在 system 路由下（路径含 /dept 前缀）
system_router.include_router(DeptRouter().router, tags=["部门管理"])

# 日志管理路由
# 直接挂在 system 路由下（路径含 /login-logs、/operation-logs、/system-logs 前缀）
system_router.include_router(LogRouter().router, tags=["日志管理"])

# 系统监控路由
# 直接挂在 system 路由下（在线用户、地图、卡片列表等 stub 接口）
system_router.include_router(MonitorRouter().router, tags=["系统监控"])

__all__ = ["system_router"]
