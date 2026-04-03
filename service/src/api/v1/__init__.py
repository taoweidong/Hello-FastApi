"""System API package - 路由聚合模块。

该模块负责聚合所有系统级别的 API 路由，包括认证、用户、角色和权限管理。
"""

from fastapi import APIRouter

from src.api.v1.auth_routes import router as auth_router
from src.api.v1.menu_routes import menu_router
from src.api.v1.permission_routes import permission_router
from src.api.v1.role_routes import role_router
from src.api.v1.system_routes import system_extra_router
from src.api.v1.user_routes import router as user_router

# 创建系统级路由聚合器
system_router = APIRouter()

# 认证路由直接挂在 system 路由下（无额外前缀）
# 提供登录、注册、登出、刷新令牌等接口
system_router.include_router(auth_router, tags=["认证管理"])

# 用户管理路由
# 前缀: /user
# 提供用户增删改查、密码管理等功能
system_router.include_router(user_router, prefix="/user", tags=["用户管理"])

# 角色管理路由
# 前缀: /role
# 提供角色增删改查、权限分配等功能
system_router.include_router(role_router, prefix="/role", tags=["角色管理"])

# 权限管理路由
# 前缀: /permission
# 提供权限增删改查等功能
system_router.include_router(permission_router, prefix="/permission", tags=["权限管理"])

# 菜单管理路由
# 前缀: /menu
# 提供菜单增删改查、菜单树获取等功能
system_router.include_router(menu_router, prefix="/menu", tags=["菜单管理"])

# 系统管理扩展路由（部门、日志等）
# 直接挂在 system 路由下（无额外前缀）
system_router.include_router(system_extra_router, tags=["系统管理"])

__all__ = ["system_router"]
