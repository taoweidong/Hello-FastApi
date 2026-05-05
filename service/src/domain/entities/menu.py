"""菜单领域实体。

定义菜单的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
菜单元数据已拆分到 MenuMetaEntity。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.domain.entities.menu_meta import MenuMetaEntity


@dataclass
class MenuEntity:
    """菜单领域实体。

    Attributes:
        id: 菜单唯一标识（32位UUID字符串）
        menu_type: 菜单类型(0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限)
        name: 菜单名称(唯一)
        rank: 排序号
        path: 路由路径
        component: 组件路径
        is_active: 是否启用
        method: HTTP方法(GET/POST/PUT/DELETE)，用于PERMISSION类型
        creator_id: 创建人ID
        modifier_id: 修改人ID
        parent_id: 父菜单ID
        meta_id: 菜单元数据ID(一对一关联sys_menumeta)
        created_time: 创建时间
        updated_time: 更新时间
        description: 描述
        meta: 菜单元数据（一对一关系）
    """

    # 类型常量
    DIRECTORY = 0
    MENU_PAGE = 1
    PERMISSION = 2

    id: str
    menu_type: int = 0
    name: str = ""
    rank: int = 0
    path: str = ""
    component: str | None = None
    is_active: int = 1
    method: str | None = None
    creator_id: str | None = None
    modifier_id: str | None = None
    parent_id: str | None = None
    meta_id: str = ""
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None
    meta: MenuMetaEntity | None = field(default=None, repr=False)

    # ---- 状态查询属性 ----

    @property
    def is_directory(self) -> bool:
        """是否为目录类型。"""
        return self.menu_type == self.DIRECTORY

    @property
    def is_menu_page(self) -> bool:
        """是否为菜单页面类型。"""
        return self.menu_type == self.MENU_PAGE

    @property
    def is_permission(self) -> bool:
        """是否为权限类型。"""
        return self.menu_type == self.PERMISSION

    @property
    def is_active_menu(self) -> bool:
        """是否启用。"""
        return self.is_active == 1

    # ---- 业务规则方法 ----

    def is_circular_reference(self, parent_id: str | None) -> bool:
        """检查是否会造成循环引用（自身设为自己的子菜单）。"""
        return parent_id == self.id

    # ---- 状态变更方法 ----

    def update_info(
        self,
        *,
        menu_type: int | None = None,
        name: str | None = None,
        path: str | None = None,
        component: str | None = None,
        rank: int | None = None,
        is_active: int | None = None,
        method: str | None = None,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> None:
        """有条件地更新菜单信息。"""
        if menu_type is not None:
            self.menu_type = menu_type
        if name is not None:
            self.name = name
        if path is not None:
            self.path = path
        if component is not None:
            self.component = component
        if rank is not None:
            self.rank = rank
        if is_active is not None:
            self.is_active = is_active
        if method is not None:
            self.method = method
        if parent_id is not None:
            self.parent_id = parent_id
        if description is not None:
            self.description = description

    # ---- 工厂方法 ----

    @classmethod
    def create_new(
        cls,
        name: str,
        menu_type: int = 0,
        path: str = "",
        component: str | None = None,
        rank: int = 0,
        is_active: int = 1,
        method: str | None = None,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> MenuEntity:
        """创建新菜单实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            name=name,
            menu_type=menu_type,
            path=path,
            component=component,
            rank=rank,
            is_active=is_active,
            method=method,
            parent_id=parent_id,
            description=description,
        )
