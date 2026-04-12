"""菜单领域实体。

定义菜单的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
菜单元数据已拆分到 MenuMetaEntity。
"""

from dataclasses import dataclass
from datetime import datetime


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
    """

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
