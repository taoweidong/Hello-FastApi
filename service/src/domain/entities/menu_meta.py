"""菜单元数据领域实体。

定义菜单元数据的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
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

    # ---- 状态变更方法 ----

    def update_info(
        self,
        *,
        title: str | None = None,
        icon: str | None = None,
        r_svg_name: str | None = None,
        is_show_menu: int | None = None,
        is_show_parent: int | None = None,
        is_keepalive: int | None = None,
        frame_url: str | None = None,
        frame_loading: int | None = None,
        transition_enter: str | None = None,
        transition_leave: str | None = None,
        is_hidden_tag: int | None = None,
        fixed_tag: int | None = None,
        dynamic_level: int | None = None,
        description: str | None = None,
    ) -> None:
        """有条件地更新菜单元数据信息。"""
        if title is not None:
            self.title = title
        if icon is not None:
            self.icon = icon
        if r_svg_name is not None:
            self.r_svg_name = r_svg_name
        if is_show_menu is not None:
            self.is_show_menu = is_show_menu
        if is_show_parent is not None:
            self.is_show_parent = is_show_parent
        if is_keepalive is not None:
            self.is_keepalive = is_keepalive
        if frame_url is not None:
            self.frame_url = frame_url
        if frame_loading is not None:
            self.frame_loading = frame_loading
        if transition_enter is not None:
            self.transition_enter = transition_enter
        if transition_leave is not None:
            self.transition_leave = transition_leave
        if is_hidden_tag is not None:
            self.is_hidden_tag = is_hidden_tag
        if fixed_tag is not None:
            self.fixed_tag = fixed_tag
        if dynamic_level is not None:
            self.dynamic_level = dynamic_level
        if description is not None:
            self.description = description

    # ---- 工厂方法 ----

    @classmethod
    def create_new(
        cls,
        title: str,
        icon: str = "",
        r_svg_name: str = "",
        is_show_menu: int = 1,
        is_show_parent: int = 0,
        is_keepalive: int = 0,
        frame_url: str = "",
        frame_loading: int = 1,
        transition_enter: str = "",
        transition_leave: str = "",
        is_hidden_tag: int = 0,
        fixed_tag: int = 0,
        dynamic_level: int = 0,
    ) -> MenuMetaEntity:
        """创建新菜单元数据实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            title=title,
            icon=icon,
            r_svg_name=r_svg_name,
            is_show_menu=is_show_menu,
            is_show_parent=is_show_parent,
            is_keepalive=is_keepalive,
            frame_url=frame_url,
            frame_loading=frame_loading,
            transition_enter=transition_enter,
            transition_leave=transition_leave,
            is_hidden_tag=is_hidden_tag,
            fixed_tag=fixed_tag,
            dynamic_level=dynamic_level,
        )
