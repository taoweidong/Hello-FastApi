"""菜单领域实体。

定义菜单的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MenuEntity:
    """菜单领域实体。

    Attributes:
        id: 菜单唯一标识（36位UUID字符串）
        name: 菜单名称
        path: 路由路径（可选）
        component: 组件路径（可选）
        icon: 图标（可选）
        title: 显示标题（可选）
        show_link: 是否显示（0-隐藏, 1-显示）
        parent_id: 父菜单ID（可选）
        order_num: 排序号
        permissions: 关联权限编码，逗号分隔（可选）
        status: 状态（0-禁用, 1-启用）
        menu_type: 菜单类型（0-菜单, 1-iframe, 2-外链, 3-按钮）
        redirect: 重定向路径（可选）
        extra_icon: 菜单名称右侧额外图标（可选）
        enter_transition: 进场动画（可选）
        leave_transition: 离场动画（可选）
        active_path: 激活菜单路径（可选）
        frame_src: iframe链接地址（可选）
        frame_loading: iframe首次加载动画
        keep_alive: 是否缓存页面
        hidden_tag: 禁止添加到标签页
        fixed_tag: 固定标签页
        show_parent: 是否显示父级菜单
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: str
    name: str
    path: str | None = None
    component: str | None = None
    icon: str | None = None
    title: str | None = None
    show_link: int = 1
    parent_id: str | None = None
    order_num: int = 0
    permissions: str | None = None
    status: int = 1
    menu_type: int = 0
    redirect: str | None = None
    extra_icon: str | None = None
    enter_transition: str | None = None
    leave_transition: str | None = None
    active_path: str | None = None
    frame_src: str | None = None
    frame_loading: bool = True
    keep_alive: bool = False
    hidden_tag: bool = False
    fixed_tag: bool = False
    show_parent: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_visible(self) -> bool:
        """是否可见（show_link=1表示显示）。"""
        return self.show_link == 1

    @property
    def is_active(self) -> bool:
        """是否启用（status=1表示启用）。"""
        return self.status == 1
