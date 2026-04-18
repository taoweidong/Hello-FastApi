"""应用层 - 菜单服务。

提供菜单相关的业务逻辑，包括Menu+MenuMeta联合CRUD、菜单树构建等。
"""

from src.application.dto.menu_dto import MenuCreateDTO, MenuMetaDTO, MenuResponseDTO, MenuUpdateDTO
from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.infrastructure.cache.cache_service import CacheService


class MenuService:
    """菜单领域操作的应用服务。"""

    def __init__(self, menu_repo: MenuRepositoryInterface, cache_service: CacheService | None = None):
        self.menu_repo = menu_repo
        self.cache_service = cache_service

    async def _get_all_menus(self) -> list[MenuEntity]:
        """获取所有菜单（带缓存）。"""
        # 尝试从缓存获取
        if self.cache_service is not None:
            cached = await self.cache_service.get_all_menus()
            if cached is not None:
                return [self._dict_to_entity(m) for m in cached]

        # 缓存未命中，查询数据库
        menus = await self.menu_repo.get_all()

        # 写入缓存
        if self.cache_service is not None:
            await self.cache_service.set_all_menus([self._entity_to_dict(m) for m in menus])

        return menus

    async def get_menu_tree(self) -> list[dict]:
        """获取完整菜单树。"""
        all_menus = await self._get_all_menus()
        return self._build_tree(all_menus, None)

    async def get_menu_list(self) -> list[dict]:
        """获取扁平菜单列表。"""
        all_menus = await self._get_all_menus()
        return [self._to_response(m) for m in all_menus]

    async def get_user_menus(self, user_id: str, user_roles: list | None = None) -> list[dict]:
        """获取用户可访问的菜单（根据角色菜单过滤）。"""
        all_menus = await self._get_all_menus()
        return self._build_tree(all_menus, None)

    async def create_menu(self, dto: MenuCreateDTO) -> MenuResponseDTO:
        """创建菜单（同时创建MenuMeta）。"""
        # 验证名称唯一性
        existing = await self.menu_repo.get_by_name(dto.name)
        if existing:
            raise ConflictError(f"菜单名称 '{dto.name}' 已存在")

        # 验证父菜单
        parent_id = dto.parentId
        if parent_id:
            parent = await self.menu_repo.get_by_id(parent_id)
            if not parent:
                raise NotFoundError("父菜单不存在")

        # 创建MenuMeta
        meta_entity = MenuMetaEntity.create_new(
            title=dto.title or dto.name,
            icon=dto.icon or "",
            r_svg_name=dto.rSvgName or "",
            is_show_menu=dto.isShowMenu if dto.isShowMenu is not None else 1,
            is_show_parent=dto.isShowParent if dto.isShowParent is not None else 0,
            is_keepalive=dto.isKeepalive if dto.isKeepalive is not None else 0,
            frame_url=dto.frameUrl or "",
            frame_loading=dto.frameLoading if dto.frameLoading is not None else 1,
            transition_enter=dto.transitionEnter or "",
            transition_leave=dto.transitionLeave or "",
            is_hidden_tag=dto.isHiddenTag if dto.isHiddenTag is not None else 0,
            fixed_tag=dto.fixedTag if dto.fixedTag is not None else 0,
            dynamic_level=dto.dynamicLevel if dto.dynamicLevel is not None else 0,
        )
        created_meta = await self.menu_repo.create_meta(meta_entity)

        # 创建Menu
        menu_entity = MenuEntity.create_new(
            name=dto.name,
            menu_type=dto.menuType if dto.menuType is not None else 0,
            path=dto.path or "",
            component=dto.component,
            rank=dto.rank if dto.rank is not None else 0,
            is_active=dto.isActive if dto.isActive is not None else 1,
            method=dto.method,
            parent_id=parent_id,
            description=dto.description,
        )
        menu_entity.meta_id = created_meta.id
        created_menu = await self.menu_repo.create(menu_entity)

        # 重新获取以加载meta关系
        loaded = await self.menu_repo.get_by_id(created_menu.id)
        if loaded is None:
            raise NotFoundError("菜单创建后无法加载")
        await self._invalidate_menu_cache()
        return self._to_response_dto(loaded)

    async def update_menu(self, menu_id: str, dto: MenuUpdateDTO) -> MenuResponseDTO:
        """更新菜单（同时更新MenuMeta）。"""
        menu = await self.menu_repo.get_by_id(menu_id)
        if not menu:
            raise NotFoundError("菜单不存在")

        # 检查循环引用
        if dto.parentId is not None:
            pid = dto.parentId
            if pid == menu_id:
                raise ConflictError("不能将菜单设置为自己的子菜单")
            if pid:
                parent = await self.menu_repo.get_by_id(pid)
                if not parent:
                    raise NotFoundError("父菜单不存在")
                menu.parent_id = pid
            else:
                menu.parent_id = None

        # 更新Menu基本字段
        if dto.name is not None:
            # 检查名称唯一性
            existing = await self.menu_repo.get_by_name(dto.name)
            if existing and existing.id != menu_id:
                raise ConflictError(f"菜单名称 '{dto.name}' 已存在")

        menu.update_info(
            menu_type=dto.menuType,
            name=dto.name,
            path=dto.path,
            component=dto.component,
            rank=dto.rank,
            is_active=dto.isActive,
            method=dto.method,
            description=dto.description,
        )
        await self.menu_repo.update(menu)

        # 更新MenuMeta
        meta = menu.meta
        if meta:
            meta.update_info(
                title=dto.title,
                icon=dto.icon,
                r_svg_name=dto.rSvgName,
                is_show_menu=dto.isShowMenu,
                is_show_parent=dto.isShowParent,
                is_keepalive=dto.isKeepalive,
                frame_url=dto.frameUrl,
                frame_loading=dto.frameLoading,
                transition_enter=dto.transitionEnter,
                transition_leave=dto.transitionLeave,
                is_hidden_tag=dto.isHiddenTag,
                fixed_tag=dto.fixedTag,
                dynamic_level=dto.dynamicLevel,
            )
            await self.menu_repo.update_meta(meta)

        # 重新获取
        updated = await self.menu_repo.get_by_id(menu_id)
        if updated is None:
            raise NotFoundError("菜单不存在")
        await self._invalidate_menu_cache()
        return self._to_response_dto(updated)

    async def delete_menu(self, menu_id: str) -> bool:
        """删除菜单（同时删除关联的MenuMeta）。"""
        menu = await self.menu_repo.get_by_id(menu_id)
        if not menu:
            raise NotFoundError("菜单不存在")

        # 检查子菜单
        children = await self.menu_repo.get_by_parent_id(menu_id)
        if children:
            raise ConflictError("该菜单下有子菜单，请先删除子菜单")

        # 删除关联的meta
        meta_id = menu.meta_id
        result = await self.menu_repo.delete(menu_id)
        if meta_id:
            await self.menu_repo.delete_meta(meta_id)

        await self._invalidate_menu_cache()
        return result

    async def _invalidate_menu_cache(self) -> None:
        """使菜单全量缓存失效。"""
        if self.cache_service is not None:
            await self.cache_service.invalidate_all_menus()

    def _entity_to_dict(self, menu: MenuEntity) -> dict:
        """将菜单实体转为可序列化的字典。"""
        result = {
            "id": menu.id, "menu_type": menu.menu_type, "name": menu.name,
            "rank": menu.rank, "path": menu.path, "component": menu.component,
            "is_active": menu.is_active, "method": menu.method,
            "creator_id": menu.creator_id, "modifier_id": menu.modifier_id,
            "parent_id": menu.parent_id, "meta_id": menu.meta_id,
            "created_time": menu.created_time.isoformat() if menu.created_time else None,
            "updated_time": menu.updated_time.isoformat() if menu.updated_time else None,
            "description": menu.description,
        }
        if menu.meta:
            result["meta"] = {
                "id": menu.meta.id, "title": menu.meta.title, "icon": menu.meta.icon,
                "r_svg_name": menu.meta.r_svg_name, "is_show_menu": menu.meta.is_show_menu,
                "is_show_parent": menu.meta.is_show_parent, "is_keepalive": menu.meta.is_keepalive,
                "frame_url": menu.meta.frame_url, "frame_loading": menu.meta.frame_loading,
                "transition_enter": menu.meta.transition_enter,
                "transition_leave": menu.meta.transition_leave,
                "is_hidden_tag": menu.meta.is_hidden_tag, "fixed_tag": menu.meta.fixed_tag,
                "dynamic_level": menu.meta.dynamic_level,
            }
        return result

    def _dict_to_entity(self, data: dict) -> MenuEntity:
        """将序列化的字典转回菜单实体。"""
        meta_data = data.pop("meta", None)
        meta_entity = None
        if meta_data:
            meta_entity = MenuMetaEntity(
                id=meta_data["id"], title=meta_data["title"], icon=meta_data["icon"],
                r_svg_name=meta_data["r_svg_name"], is_show_menu=meta_data["is_show_menu"],
                is_show_parent=meta_data["is_show_parent"], is_keepalive=meta_data["is_keepalive"],
                frame_url=meta_data["frame_url"], frame_loading=meta_data["frame_loading"],
                transition_enter=meta_data["transition_enter"],
                transition_leave=meta_data["transition_leave"],
                is_hidden_tag=meta_data["is_hidden_tag"], fixed_tag=meta_data["fixed_tag"],
                dynamic_level=meta_data["dynamic_level"],
            )
        from datetime import datetime as dt, timezone
        created_time = dt.fromisoformat(data.pop("created_time")) if data.get("created_time") else None
        updated_time = dt.fromisoformat(data.pop("updated_time")) if data.get("updated_time") else None
        menu = MenuEntity(
            id=data["id"], menu_type=data["menu_type"], name=data["name"],
            rank=data["rank"], path=data["path"], component=data["component"],
            is_active=data["is_active"], method=data["method"],
            creator_id=data["creator_id"], modifier_id=data["modifier_id"],
            parent_id=data["parent_id"], meta_id=data["meta_id"],
            created_time=created_time, updated_time=updated_time,
            description=data["description"],
        )
        menu._meta = meta_entity
        return menu

    def _build_tree(self, menus: list[MenuEntity], parent_id: str | None) -> list[dict]:
        """构建菜单树。"""
        tree = []
        for menu in menus:
            if menu.parent_id == parent_id:
                node = self._to_response(menu)
                node["children"] = self._build_tree(menus, menu.id)
                tree.append(node)
        # 按rank排序
        return sorted(tree, key=lambda x: x.get("rank", 0))

    def _to_response(self, menu: MenuEntity) -> dict:
        """将菜单实体转为响应字典（含嵌套meta）。"""
        meta_dict = None
        if menu.meta:
            meta_dict = {
                "id": menu.meta.id,
                "title": menu.meta.title or "",
                "icon": menu.meta.icon or "",
                "rSvgName": menu.meta.r_svg_name or "",
                "isShowMenu": menu.meta.is_show_menu,
                "isShowParent": menu.meta.is_show_parent,
                "isKeepalive": menu.meta.is_keepalive,
                "frameUrl": menu.meta.frame_url or "",
                "frameLoading": menu.meta.frame_loading,
                "transitionEnter": menu.meta.transition_enter or "",
                "transitionLeave": menu.meta.transition_leave or "",
                "isHiddenTag": menu.meta.is_hidden_tag,
                "fixedTag": menu.meta.fixed_tag,
                "dynamicLevel": menu.meta.dynamic_level,
            }

        return {
            "id": menu.id,
            "parentId": menu.parent_id or 0,
            "menuType": menu.menu_type,
            "name": menu.name,
            "path": menu.path or "",
            "component": menu.component or "",
            "rank": menu.rank,
            "isActive": menu.is_active,
            "method": menu.method or "",
            "metaId": menu.meta_id or "",
            "meta": meta_dict or {"title": menu.name, "isShowMenu": 1, "isKeepalive": 0},
            "creatorId": menu.creator_id,
            "modifierId": menu.modifier_id,
            "createdTime": menu.created_time.isoformat() if menu.created_time else None,
            "updatedTime": menu.updated_time.isoformat() if menu.updated_time else None,
            "description": menu.description or "",
            "children": [],
        }

    def _to_response_dto(self, menu: MenuEntity) -> MenuResponseDTO:
        """将菜单实体转为 MenuResponseDTO。"""
        meta_dto = None
        if menu.meta:
            meta_dto = MenuMetaDTO(
                id=menu.meta.id,
                title=menu.meta.title,
                icon=menu.meta.icon,
                rSvgName=menu.meta.r_svg_name,
                isShowMenu=menu.meta.is_show_menu,
                isShowParent=menu.meta.is_show_parent,
                isKeepalive=menu.meta.is_keepalive,
                frameUrl=menu.meta.frame_url,
                frameLoading=menu.meta.frame_loading,
                transitionEnter=menu.meta.transition_enter,
                transitionLeave=menu.meta.transition_leave,
                isHiddenTag=menu.meta.is_hidden_tag,
                fixedTag=menu.meta.fixed_tag,
                dynamicLevel=menu.meta.dynamic_level,
            )

        return MenuResponseDTO(
            id=menu.id,
            parentId=menu.parent_id,
            menuType=menu.menu_type,
            name=menu.name,
            path=menu.path or "",
            component=menu.component,
            rank=menu.rank,
            isActive=menu.is_active,
            method=menu.method,
            metaId=menu.meta_id or "",
            meta=meta_dto,
            creatorId=menu.creator_id,
            modifierId=menu.modifier_id,
            createdTime=menu.created_time,
            updatedTime=menu.updated_time,
            description=menu.description,
        )
