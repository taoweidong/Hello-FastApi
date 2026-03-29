"""应用层 - 菜单领域的数据传输对象。"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MenuCreateDTO(BaseModel):
    """创建菜单请求"""
    parentId: int = 0  # 父菜单ID，0表示顶级菜单
    menuType: int = 0  # 菜单类型（0-菜单, 1-iframe, 2-外链, 3-按钮）
    title: str = Field(max_length=64)  # 菜单名称
    name: str | None = Field(default=None, max_length=64)  # 路由name
    path: str | None = Field(default=None, max_length=256)  # 路由路径
    component: str | None = Field(default=None, max_length=256)  # 组件路径
    rank: int = 99  # 排序
    redirect: str | None = Field(default=None, max_length=256)  # 重定向路径
    icon: str | None = Field(default=None, max_length=64)  # 图标
    extraIcon: str | None = Field(default=None, max_length=64)  # 额外图标
    enterTransition: str | None = Field(default=None, max_length=64)  # 进场动画
    leaveTransition: str | None = Field(default=None, max_length=64)  # 离场动画
    activePath: str | None = Field(default=None, max_length=256)  # 激活路径
    auths: str | None = Field(default=None, max_length=500)  # 权限标识
    frameSrc: str | None = Field(default=None, max_length=500)  # iframe地址
    frameLoading: bool = True  # iframe加载状态
    keepAlive: bool = False  # 是否缓存
    hiddenTag: bool = False  # 是否隐藏标签
    fixedTag: bool = False  # 是否固定标签
    showLink: bool = True  # 是否显示
    showParent: bool = False  # 是否显示父级


class MenuUpdateDTO(BaseModel):
    """更新菜单请求"""
    parentId: int | None = None
    menuType: int | None = None
    title: str | None = Field(default=None, max_length=64)
    name: str | None = Field(default=None, max_length=64)
    path: str | None = Field(default=None, max_length=256)
    component: str | None = Field(default=None, max_length=256)
    rank: int | None = None
    redirect: str | None = Field(default=None, max_length=256)
    icon: str | None = Field(default=None, max_length=64)
    extraIcon: str | None = Field(default=None, max_length=64)
    enterTransition: str | None = Field(default=None, max_length=64)
    leaveTransition: str | None = Field(default=None, max_length=64)
    activePath: str | None = Field(default=None, max_length=256)
    auths: str | None = Field(default=None, max_length=500)
    frameSrc: str | None = Field(default=None, max_length=500)
    frameLoading: bool | None = None
    keepAlive: bool | None = None
    hiddenTag: bool | None = None
    fixedTag: bool | None = None
    showLink: bool | None = None
    showParent: bool | None = None


class MenuResponseDTO(BaseModel):
    """菜单响应"""
    id: int
    parentId: int = 0
    menuType: int = 0
    title: str
    name: str | None = None
    path: str | None = None
    component: str | None = None
    rank: int = 99
    redirect: str | None = None
    icon: str | None = None
    extraIcon: str | None = None
    enterTransition: str | None = None
    leaveTransition: str | None = None
    activePath: str | None = None
    auths: str | None = None
    frameSrc: str | None = None
    frameLoading: bool = True
    keepAlive: bool = False
    hiddenTag: bool = False
    fixedTag: bool = False
    showLink: bool = True
    showParent: bool = False
    children: list["MenuResponseDTO"] = []

    model_config = {"from_attributes": True}


# 解决前向引用
MenuResponseDTO.model_rebuild()
