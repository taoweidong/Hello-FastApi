"""应用层 - 菜单领域的数据传输对象。"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MenuCreateDTO(BaseModel):
    """创建菜单请求"""
    name: str = Field(max_length=64)
    path: str | None = Field(default=None, max_length=256)
    component: str | None = Field(default=None, max_length=256)
    icon: str | None = Field(default=None, max_length=64)
    title: str | None = Field(default=None, max_length=64)
    showLink: int = 1
    parentId: str | None = None
    permissions: list[str] = []
    order: int = 0


class MenuUpdateDTO(BaseModel):
    """更新菜单请求"""
    name: str | None = Field(default=None, max_length=64)
    path: str | None = Field(default=None, max_length=256)
    component: str | None = Field(default=None, max_length=256)
    icon: str | None = Field(default=None, max_length=64)
    title: str | None = Field(default=None, max_length=64)
    showLink: int | None = None
    parentId: str | None = None
    permissions: list[str] | None = None
    order: int | None = None


class MenuResponseDTO(BaseModel):
    """菜单响应"""
    id: str
    name: str
    path: str | None = None
    component: str | None = None
    icon: str | None = None
    title: str | None = None
    showLink: int = 1
    parentId: str | None = None
    permissions: list[str] = []
    order: int = 0
    status: int = 1
    children: list["MenuResponseDTO"] = []
    createTime: datetime | None = None
    updateTime: datetime | None = None

    model_config = {"from_attributes": True}


# 解决前向引用
MenuResponseDTO.model_rebuild()
