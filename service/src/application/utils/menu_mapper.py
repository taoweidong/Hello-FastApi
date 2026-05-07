"""菜单实体与序列化字典之间的转换工具。

用于缓存序列化/反序列化，避免 MenuService 和 AuthService 中的重复代码。
"""

from datetime import datetime as dt

from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity


def menu_entity_to_dict(menu: MenuEntity) -> dict:
    """将菜单实体转为可序列化的字典（用于缓存存储）。"""
    result: dict = {
        "id": menu.id,
        "menu_type": menu.menu_type,
        "name": menu.name,
        "rank": menu.rank,
        "path": menu.path,
        "component": menu.component,
        "is_active": menu.is_active,
        "method": menu.method,
        "creator_id": menu.creator_id,
        "modifier_id": menu.modifier_id,
        "parent_id": menu.parent_id,
        "meta_id": menu.meta_id,
        "created_time": menu.created_time.isoformat() if menu.created_time else None,
        "updated_time": menu.updated_time.isoformat() if menu.updated_time else None,
        "description": menu.description,
    }
    if menu.meta:
        result["meta"] = {
            "id": menu.meta.id,
            "title": menu.meta.title,
            "icon": menu.meta.icon,
            "r_svg_name": menu.meta.r_svg_name,
            "is_show_menu": menu.meta.is_show_menu,
            "is_show_parent": menu.meta.is_show_parent,
            "is_keepalive": menu.meta.is_keepalive,
            "frame_url": menu.meta.frame_url,
            "frame_loading": menu.meta.frame_loading,
            "transition_enter": menu.meta.transition_enter,
            "transition_leave": menu.meta.transition_leave,
            "is_hidden_tag": menu.meta.is_hidden_tag,
            "fixed_tag": menu.meta.fixed_tag,
            "dynamic_level": menu.meta.dynamic_level,
        }
    return result


def menu_dict_to_entity(data: dict) -> MenuEntity:
    """将序列化的字典转回菜单实体（用于从缓存恢复）。"""
    meta_data = data.get("meta")
    meta_entity: MenuMetaEntity | None = None
    if meta_data:
        meta_entity = MenuMetaEntity(
            id=meta_data["id"],
            title=meta_data["title"],
            icon=meta_data["icon"],
            r_svg_name=meta_data["r_svg_name"],
            is_show_menu=meta_data["is_show_menu"],
            is_show_parent=meta_data["is_show_parent"],
            is_keepalive=meta_data["is_keepalive"],
            frame_url=meta_data["frame_url"],
            frame_loading=meta_data["frame_loading"],
            transition_enter=meta_data["transition_enter"],
            transition_leave=meta_data["transition_leave"],
            is_hidden_tag=meta_data["is_hidden_tag"],
            fixed_tag=meta_data["fixed_tag"],
            dynamic_level=meta_data["dynamic_level"],
        )
    created_time = dt.fromisoformat(data["created_time"]) if data.get("created_time") else None
    updated_time = dt.fromisoformat(data["updated_time"]) if data.get("updated_time") else None
    menu = MenuEntity(
        id=data["id"],
        menu_type=data["menu_type"],
        name=data["name"],
        rank=data["rank"],
        path=data["path"],
        component=data["component"],
        is_active=data["is_active"],
        method=data["method"],
        creator_id=data["creator_id"],
        modifier_id=data["modifier_id"],
        parent_id=data["parent_id"],
        meta_id=data["meta_id"],
        created_time=created_time,
        updated_time=updated_time,
        description=data["description"],
    )
    menu.meta = meta_entity
    return menu
