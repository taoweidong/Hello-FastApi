"""菜单树工具函数（纯函数，供角色授权与动态路由使用）。"""

from src.domain.entities.menu import MenuEntity


def build_parent_map(all_menus: list[MenuEntity]) -> dict[str, str | None]:
    """菜单 ID → 父 ID 映射。"""
    return {m.id: m.parent_id for m in all_menus}


def complete_ancestor_ids(
    menu_ids: list[str],
    parent_map: dict[str, str | None],
) -> list[str]:
    """补全菜单 ID 集合的全部祖先节点，返回去重后的列表。

    角色授权的防御层：前端父子联动模式回传的是"全选 + 半选"，若客户端
    缺陷导致半选父级丢失，动态路由会出现孤儿页面（页面节点的父目录不在
    授权集合中，_build_route_tree 无法挂载）。服务端据此补全祖先链。
    未知 ID（不在菜单表中）静默忽略。
    """
    result: set[str] = set()
    for mid in menu_ids:
        if mid not in parent_map:
            continue
        result.add(mid)
        seen = {mid}
        parent = parent_map[mid]
        while parent and parent in parent_map and parent not in seen:
            result.add(parent)
            seen.add(parent)
            parent = parent_map[parent]
    return list(result)
