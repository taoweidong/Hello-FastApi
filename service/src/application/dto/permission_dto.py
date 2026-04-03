"""应用层 - 权限领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field


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
