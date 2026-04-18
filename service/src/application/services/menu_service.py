"""应用层 - 菜单服务。

提供菜单相关的业务逻辑，包括Menu+MenuMeta联合CRUD、菜单树构建等。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.menu_dto import MenuCreateDTO, MenuMetaDTO, MenuResponseDTO, MenuUpdateDTO
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.infrastructure.database.models import Menu, MenuMeta


class MenuService:
    """菜单领域操作的应用服务。"""

    def __init__(self, session: AsyncSession, menu_repo: MenuRepositoryInterface):
        self.session = session
        self.menu_repo = menu_repo

    async def get_menu_tree(self, session: AsyncSession | None = None) -> list[dict]:
        """获取完整菜单树。"""
        all_menus = await self.menu_repo.get_all(session or self.session)
        return self._build_tree(all_menus, None)

    async def get_menu_list(self, session: AsyncSession | None = None) -> list[dict]:
        """获取扁平菜单列表。"""
        all_menus = await self.menu_repo.get_all(session or self.session)
        return [self._to_response(m) for m in all_menus]

    async def get_user_menus(self, user_id: str, user_roles: list | None = None, session: AsyncSession | None = None) -> list[dict]:
        """获取用户可访问的菜单（根据角色菜单过滤）。"""
        all_menus = await self.menu_repo.get_all(session or self.session)
        return self._build_tree(all_menus, None)

    async def create_menu(self, dto: MenuCreateDTO, session: AsyncSession | None = None) -> MenuResponseDTO:
        """创建菜单（同时创建MenuMeta）。"""
        sess = session or self.session

        # 验证名称唯一性
        existing = await self.menu_repo.get_by_name(dto.name, session=sess)
        if existing:
            raise ConflictError(f"菜单名称 '{dto.name}' 已存在")

        # 验证父菜单
        parent_id = dto.parentId
        if parent_id:
            parent = await self.menu_repo.get_by_id(parent_id, session=sess)
            if not parent:
                raise NotFoundError("父菜单不存在")

        # 创建MenuMeta
        meta = MenuMeta(
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
        sess.add(meta)
        await sess.flush()

        # 创建Menu
        menu = Menu(
            name=dto.name,
            parent_id=parent_id,
            menu_type=dto.menuType if dto.menuType is not None else 0,
            path=dto.path or "",
            component=dto.component or "",
            rank=dto.rank if dto.rank is not None else 0,
            is_active=dto.isActive if dto.isActive is not None else 1,
            method=dto.method,
            meta_id=meta.id,
            description=dto.description,
        )
        sess.add(menu)
        await sess.flush()

        # 重新获取以加载meta关系
        created = await self.menu_repo.get_by_id(menu.id, session=sess)
        if created is None:
            raise NotFoundError("菜单创建后无法加载")
        return self._to_response_dto(created)

    async def update_menu(self, menu_id: str, dto: MenuUpdateDTO, session: AsyncSession | None = None) -> MenuResponseDTO:
        """更新菜单（同时更新MenuMeta）。"""
        sess = session or self.session
        menu = await self.menu_repo.get_by_id(menu_id, session=sess)
        if not menu:
            raise NotFoundError("菜单不存在")

        # 检查循环引用
        if dto.parentId is not None:
            pid = dto.parentId
            if pid == menu_id:
                raise ConflictError("不能将菜单设置为自己的子菜单")
            if pid:
                parent = await self.menu_repo.get_by_id(pid, session=sess)
                if not parent:
                    raise NotFoundError("父菜单不存在")
                menu.parent_id = pid
            else:
                menu.parent_id = None

        # 更新Menu基本字段
        if dto.menuType is not None:
            menu.menu_type = dto.menuType
        if dto.name is not None:
            # 检查名称唯一性
            existing = await self.menu_repo.get_by_name(dto.name, session=sess)
            if existing and existing.id != menu_id:
                raise ConflictError(f"菜单名称 '{dto.name}' 已存在")
            menu.name = dto.name
        if dto.path is not None:
            menu.path = dto.path
        if dto.component is not None:
            menu.component = dto.component
        if dto.rank is not None:
            menu.rank = dto.rank
        if dto.isActive is not None:
            menu.is_active = dto.isActive
        if dto.method is not None:
            menu.method = dto.method
        if dto.description is not None:
            menu.description = dto.description

        await self.menu_repo.update(menu, session=sess)

        # 更新MenuMeta
        meta = menu.meta
        if meta:
            if dto.title is not None:
                meta.title = dto.title
            if dto.icon is not None:
                meta.icon = dto.icon
            if dto.rSvgName is not None:
                meta.r_svg_name = dto.rSvgName
            if dto.isShowMenu is not None:
                meta.is_show_menu = dto.isShowMenu
            if dto.isShowParent is not None:
                meta.is_show_parent = dto.isShowParent
            if dto.isKeepalive is not None:
                meta.is_keepalive = dto.isKeepalive
            if dto.frameUrl is not None:
                meta.frame_url = dto.frameUrl
            if dto.frameLoading is not None:
                meta.frame_loading = dto.frameLoading
            if dto.transitionEnter is not None:
                meta.transition_enter = dto.transitionEnter
            if dto.transitionLeave is not None:
                meta.transition_leave = dto.transitionLeave
            if dto.isHiddenTag is not None:
                meta.is_hidden_tag = dto.isHiddenTag
            if dto.fixedTag is not None:
                meta.fixed_tag = dto.fixedTag
            if dto.dynamicLevel is not None:
                meta.dynamic_level = dto.dynamicLevel
            await self.menu_repo.update_meta(meta, session=sess)

        await sess.flush()

        # 重新获取
        updated = await self.menu_repo.get_by_id(menu_id, session=sess)
        if updated is None:
            raise NotFoundError("菜单不存在")
        return self._to_response_dto(updated)

    async def delete_menu(self, menu_id: str, session: AsyncSession | None = None) -> bool:
        """删除菜单（同时删除关联的MenuMeta）。"""
        sess = session or self.session
        menu = await self.menu_repo.get_by_id(menu_id, session=sess)
        if not menu:
            raise NotFoundError("菜单不存在")

        # 检查子菜单
        children = await self.menu_repo.get_by_parent_id(menu_id, session=sess)
        if children:
            raise ConflictError("该菜单下有子菜单，请先删除子菜单")

        # 删除关联的meta
        meta_id = menu.meta_id
        result = await self.menu_repo.delete(menu_id, session=sess)
        if meta_id:
            await self.menu_repo.delete_meta(meta_id, session=sess)

        await sess.flush()
        return result

    def _build_tree(self, menus: list[Menu], parent_id: str | None) -> list[dict]:
        """构建菜单树。"""
        tree = []
        for menu in menus:
            if menu.parent_id == parent_id:
                node = self._to_response(menu)
                node["children"] = self._build_tree(menus, menu.id)
                tree.append(node)
        # 按rank排序
        return sorted(tree, key=lambda x: x.get("rank", 0))

    def _to_response(self, menu: Menu) -> dict:
        """将 Menu 模型转为响应字典（含嵌套meta）。"""
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

    def _to_response_dto(self, menu: Menu) -> MenuResponseDTO:
        """将 Menu 模型转为 MenuResponseDTO。"""
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
