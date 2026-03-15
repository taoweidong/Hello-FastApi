"""应用层 - RBAC 领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field


class RoleCreateDTO(BaseModel):
    """创建角色 DTO。"""

    name: str = Field(..., min_length=2, max_length=50)
    description: str | None = Field(None, max_length=255)


class RoleUpdateDTO(BaseModel):
    """更新角色 DTO。"""

    name: str | None = Field(None, min_length=2, max_length=50)
    description: str | None = Field(None, max_length=255)


class RoleResponseDTO(BaseModel):
    """角色响应 DTO。"""

    id: str
    name: str
    description: str | None = None
    permissions: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionCreateDTO(BaseModel):
    """创建权限 DTO。"""

    name: str = Field(..., min_length=2, max_length=100)
    codename: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=255)
    resource: str = Field(..., max_length=100)
    action: str = Field(..., max_length=50)


class PermissionResponseDTO(BaseModel):
    """权限响应 DTO。"""

    id: str
    name: str
    codename: str
    description: str | None = None
    resource: str
    action: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignRoleDTO(BaseModel):
    """为用户分配角色 DTO。"""

    user_id: str
    role_id: str


class AssignPermissionDTO(BaseModel):
    """为角色分配权限 DTO。"""

    role_id: str
    permission_id: str
