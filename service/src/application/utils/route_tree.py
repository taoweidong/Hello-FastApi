"""前端动态路由树构建（纯函数）。

从 AuthService 拆出：路由树/meta 是给前端纯-admin 的 presentation 结构，
不依赖任何仓储与缓存，独立成纯函数便于测试与复用。
"""

from src.application.utils.menu_mapper import menu_entity_to_dict  # noqa: F401  (re-export 保持旧引用可用)
from src.domain.entities.menu import MenuEntity


def build_meta(menu: MenuEntity) -> dict:
    """从菜单实体的 meta 字段构建前端 meta 对象。"""
    meta = menu.meta
    if meta:
        return {
            "title": meta.title or "",
            "icon": meta.icon or "",
            "rSvgName": meta.r_svg_name or "",
            "showLink": bool(meta.is_show_menu),
            "showParent": bool(meta.is_show_parent),
            "keepAlive": bool(meta.is_keepalive),
            "frameUrl": meta.frame_url or "",
            "frameLoading": bool(meta.frame_loading),
            "transition": {"enter": meta.transition_enter or "", "leave": meta.transition_leave or ""}
            if meta.transition_enter or meta.transition_leave
            else {},
            "hiddenTag": bool(meta.is_hidden_tag),
            "fixedTag": bool(meta.fixed_tag),
            "dynamicLevel": meta.dynamic_level,
        }
    # 如果没有meta，返回基本meta
    return {"title": menu.name, "showLink": True, "keepAlive": False}


def build_route_tree(
    menus: list[MenuEntity],
    parent_id: str | None = None,
    auths_map: dict[str, list[str]] | None = None,
    inherited_auths: list[str] | None = None,
) -> list[dict]:
    """将扁平菜单列表构建为嵌套路由树。

    Args:
        menus: 扁平菜单实体列表（仅 DIRECTORY/MENU 类型参与建树）
        parent_id: 当前递归的父节点 ID
        auths_map: 菜单 ID -> 按钮权限码列表（PERMISSION 子节点汇总）
        inherited_auths: 祖先路由向下传播的权限码
    """
    routes = []
    for menu in menus:
        if menu.parent_id == parent_id:
            meta = build_meta(menu)
            # 挂载当前菜单的按钮权限码列表，前端通过 meta.auths 做按钮级控制
            menu_auths = list((auths_map or {}).get(menu.id, []))
            # 祖先路由的权限码向下传播：按钮权限（PERMISSION 节点）常挂在目录菜单上
            # （如 log:view/log:delete 挂在「日志管理」目录），而真正使用 v-auth 的
            # 页面是其子路由（登录日志/操作日志）。不传播则子路由 meta.auths 为 None，
            # hasAuth 恒判假 → 页面上的删除/清空按钮被静默移除。
            for code in inherited_auths or []:
                if code not in menu_auths:
                    menu_auths.append(code)
            if menu_auths:
                meta["auths"] = menu_auths
            route = {"path": menu.path, "name": menu.name, "rank": menu.rank, "component": menu.component, "meta": meta}
            children = build_route_tree(menus, menu.id, auths_map, menu_auths)
            if children:
                route["children"] = children
            routes.append(route)
    # 按rank排序
    return sorted(routes, key=lambda r: r.get("rank", 0))
