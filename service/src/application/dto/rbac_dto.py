"""应用层 - RBAC 领域的数据传输对象。"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RoleCreateDTO(BaseModel):
    """创建角色请求"""
    name: str = Field(min_length=2, max_length=64)
    code: str = Field(min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    status: int = 1
    permissionIds: list[str] = []


class RoleUpdateDTO(BaseModel):
    """更新角色请求"""
    name: str | None = Field(default=None, min_length=2, max_length=64)
    code: str | None = Field(default=None, min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    status: int | None = None
    permissionIds: list[str] | None = None


class RoleResponseDTO(BaseModel):
    """角色响应"""
    id: str
    name: str
    code: str
    description: str | None = None
    status: int = 1
    permissions: list[dict] = []
    createTime: datetime | None = None
    updateTime: datetime | None = None

    model_config = {"from_attributes": True}


class RoleListQueryDTO(BaseModel):
    """角色列表查询"""
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    roleName: str | None = None
    status: int | None = None


class PermissionCreateDTO(BaseModel):
    """创建权限请求"""
    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    status: int = 1


class PermissionResponseDTO(BaseModel):
    """权限响应"""
    id: str
    name: str
    code: str
    category: str | None = None
    description: str | None = None
    status: int = 1
    createTime: datetime | None = None

    model_config = {"from_attributes": True}


class PermissionListQueryDTO(BaseModel):
    """权限列表查询"""
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    permissionName: str | None = None


class AssignRoleDTO(BaseModel):
    """分配角色请求"""
    user_id: str = Field(alias="userId")
    role_id: str = Field(alias="roleId")

    model_config = {"populate_by_name": True}


class AssignPermissionsDTO(BaseModel):
    """分配权限请求"""
    permissionIds: list[str]
