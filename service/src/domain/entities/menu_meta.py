"""菜单元数据领域实体。

定义菜单元数据的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MenuMetaEntity:
    """菜单元数据领域实体（显示配置）。

    Attributes:
        id: 主键UUID（32位）
        title: 菜单显示标题
        icon: 菜单图标
        r_svg_name: SVG图标名称(remix icon)
        is_show_menu: 是否在菜单中显示
        is_show_parent: 是否显示父级菜单
        is_keepalive: 是否缓存页面(keep-alive)
        frame_url: iframe内嵌链接
        frame_loading: iframe加载动画
        transition_enter: 进场动画名称
        transition_leave: 离场动画名称
        is_hidden_tag: 禁止添加到标签页
        fixed_tag: 固定标签页
        dynamic_level: 动态路由层级
        creator_id: 创建人ID
        modifier_id: 修改人ID
        created_time: 创建时间
        updated_time: 更新时间
        description: 描述
    """

    id: str
    title: str | None = None
    icon: str | None = None
    r_svg_name: str | None = None
    is_show_menu: int = 1
    is_show_parent: int = 0
    is_keepalive: int = 0
    frame_url: str | None = None
    frame_loading: int = 1
    transition_enter: str | None = None
    transition_leave: str | None = None
    is_hidden_tag: int = 0
    fixed_tag: int = 0
    dynamic_level: int = 0
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None
