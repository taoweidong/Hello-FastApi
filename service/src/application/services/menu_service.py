"""应用层 - 菜单服务。

提供菜单相关的业务逻辑，包括菜单树构建、用户菜单过滤等。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.menu_dto import MenuCreateDTO, MenuUpdateDTO
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.domain.repositories.permission_repository import PermissionRepositoryInterface
from src.infrastructure.database.models import Menu


def _norm_menu_parent_id(v: str | int | None) -> str | None:
    if v is None or v == "" or v == 0 or v == "0":
        return None
    return str(v)


class MenuService:
    """菜单领域操作的应用服务。"""

    def __init__(self, session: AsyncSession, menu_repo: MenuRepositoryInterface, perm_repo: PermissionRepositoryInterface):
        """初始化菜单服务。

        Args:
            session: 数据库会话，用于事务控制
            menu_repo: 菜单仓储接口实例
            perm_repo: 权限仓储接口实例
        """
        self.session = session
        self.menu_repo = menu_repo
        self.perm_repo = perm_repo

    async def get_menu_tree(self) -> list[dict]:
        """获取完整菜单树。"""
        all_menus = await self.menu_repo.get_all()
        return self._build_tree(all_menus, None)

    async def get_user_menus(self, user_id: str) -> list[dict]:
        """获取用户可访问的菜单（根据用户权限过滤）。

        超级用户返回所有菜单，普通用户根据权限过滤。
        """
        # 获取所有菜单
        all_menus = await self.menu_repo.get_all()

        # 获取用户的所有权限编码
        user_permissions = await self.perm_repo.get_user_permissions(user_id)
        user_perm_codes = {p.code for p in user_permissions}

        # 过滤出有权限访问的菜单
        filtered_menus = []
        for menu in all_menus:
            # 菜单没有关联权限或用户有其中任一权限则可访问
            if not menu.permissions:
                filtered_menus.append(menu)
            else:
                menu_perms = set(menu.permissions.split(","))
                if menu_perms & user_perm_codes:  # 有交集表示有权限
                    filtered_menus.append(menu)

        return self._build_tree(filtered_menus, None)

    async def create_menu(self, dto: MenuCreateDTO) -> dict:
        """创建菜单。"""
        # 如果有父菜单，验证父菜单是否存在
        pid = _norm_menu_parent_id(dto.parentId)
        if pid:
            parent = await self.menu_repo.get_by_id(pid)
            if not parent:
                raise NotFoundError("父菜单不存在")

        # 创建菜单实体，映射所有 DTO 字段到 ORM 模型
        menu = Menu(
            name=dto.name or dto.title,  # 如果没有 name，使用 title
            path=dto.path,
            component=dto.component,
            icon=dto.icon,
            title=dto.title,
            show_link=1 if dto.showLink else 0,  # bool 转 int
            parent_id=pid,
            order_num=dto.rank,
            permissions=dto.auths,
            status=1,
            # Pure Admin 扩展字段
            menu_type=dto.menuType,
            redirect=dto.redirect,
            extra_icon=dto.extraIcon,
            enter_transition=dto.enterTransition,
            leave_transition=dto.leaveTransition,
            active_path=dto.activePath,
            frame_src=dto.frameSrc,
            frame_loading=dto.frameLoading,
            keep_alive=dto.keepAlive,
            hidden_tag=dto.hiddenTag,
            fixed_tag=dto.fixedTag,
            show_parent=dto.showParent,
        )
        await self.menu_repo.create(menu)
        await self.session.flush()
        # 重新获取以确保返回完整模型
        created = await self.menu_repo.get_by_id(menu.id)
        if created is None:
            raise NotFoundError("菜单创建后无法加载")
        return self._to_response(created)

    async def update_menu(self, menu_id: str, dto: MenuUpdateDTO) -> dict:
        """更新菜单。"""
        menu = await self.menu_repo.get_by_id(menu_id)
        if not menu:
            raise NotFoundError("菜单不存在")

        # 检查是否将菜单设置为自己的子菜单（循环引用）
        # 处理父菜单ID更新
        if dto.parentId is not None:
            pid = _norm_menu_parent_id(dto.parentId)
            if pid == menu_id:
                raise ConflictError("不能将菜单设置为自己的子菜单")
            if pid:
                parent = await self.menu_repo.get_by_id(pid)
                if not parent:
                    raise NotFoundError("父菜单不存在")
                if await self._is_descendant(menu_id, pid):
                    raise ConflictError("不能将菜单设置为其子菜单的子菜单")
                menu.parent_id = pid
            else:
                menu.parent_id = None

        # 选择性更新基本字段
        if dto.name is not None:
            menu.name = dto.name
        if dto.path is not None:
            menu.path = dto.path
        if dto.component is not None:
            menu.component = dto.component
        if dto.icon is not None:
            menu.icon = dto.icon
        if dto.title is not None:
            menu.title = dto.title
        if dto.showLink is not None:
            menu.show_link = 1 if dto.showLink else 0  # bool 转 int
        if dto.auths is not None:
            menu.permissions = dto.auths
        if dto.rank is not None:
            menu.order_num = dto.rank
        if dto.status is not None:
            menu.status = dto.status

        # 选择性更新 Pure Admin 扩展字段
        if dto.menuType is not None:
            menu.menu_type = dto.menuType
        if dto.redirect is not None:
            menu.redirect = dto.redirect
        if dto.extraIcon is not None:
            menu.extra_icon = dto.extraIcon
        if dto.enterTransition is not None:
            menu.enter_transition = dto.enterTransition
        if dto.leaveTransition is not None:
            menu.leave_transition = dto.leaveTransition
        if dto.activePath is not None:
            menu.active_path = dto.activePath
        if dto.frameSrc is not None:
            menu.frame_src = dto.frameSrc
        if dto.frameLoading is not None:
            menu.frame_loading = dto.frameLoading
        if dto.keepAlive is not None:
            menu.keep_alive = dto.keepAlive
        if dto.hiddenTag is not None:
            menu.hidden_tag = dto.hiddenTag
        if dto.fixedTag is not None:
            menu.fixed_tag = dto.fixedTag
        if dto.showParent is not None:
            menu.show_parent = dto.showParent

        await self.menu_repo.update(menu)
        await self.session.flush()
        # 重新获取以确保返回完整模型
        updated = await self.menu_repo.get_by_id(menu_id)
        if updated is None:
            raise NotFoundError("菜单不存在")
        return self._to_response(updated)

    async def delete_menu(self, menu_id: str) -> bool:
        """删除菜单。"""
        # 检查菜单是否存在
        menu = await self.menu_repo.get_by_id(menu_id)
        if not menu:
            raise NotFoundError("菜单不存在")

        # 检查是否有子菜单
        children = await self.menu_repo.get_by_parent_id(menu_id)
        if children:
            raise ConflictError("该菜单下有子菜单，请先删除子菜单")

        return await self.menu_repo.delete(menu_id)

    async def _is_descendant(self, ancestor_id: str, descendant_id: str) -> bool:
        """检查 descendant_id 是否是 ancestor_id 的后代（用于防止循环引用）。"""
        children = await self.menu_repo.get_by_parent_id(descendant_id)
        for child in children:
            if child.id == ancestor_id:
                return True
            if await self._is_descendant(ancestor_id, child.id):
                return True
        return False

    def _build_tree(self, menus: list[Menu], parent_id: str | None) -> list[dict]:
        """构建菜单树。"""
        tree = []
        for menu in menus:
            if menu.parent_id == parent_id:
                node = self._to_response(menu)
                node["children"] = self._build_tree(menus, menu.id)
                tree.append(node)
        return tree

    def _to_response(self, menu: Menu) -> dict:
        """将 Menu 模型转为响应字典（Pure Admin 标准格式）。"""
        return {
            "id": menu.id,
            "parentId": menu.parent_id or 0,
            "menuType": menu.menu_type,
            "title": menu.title or menu.name,
            "name": menu.name,
            "path": menu.path or "",
            "component": menu.component or "",
            "rank": menu.order_num,
            "redirect": menu.redirect or "",
            "icon": menu.icon or "",
            "extraIcon": menu.extra_icon or "",
            "enterTransition": menu.enter_transition or "",
            "leaveTransition": menu.leave_transition or "",
            "activePath": menu.active_path or "",
            "auths": menu.permissions or "",
            "frameSrc": menu.frame_src or "",
            "frameLoading": menu.frame_loading,
            "keepAlive": menu.keep_alive,
            "hiddenTag": menu.hidden_tag,
            "fixedTag": menu.fixed_tag,
            "showLink": bool(menu.show_link),
            "showParent": menu.show_parent,
            "status": menu.status,
            "children": [],
            "createTime": menu.created_at.isoformat() if menu.created_at else None,
            "updateTime": menu.updated_at.isoformat() if menu.updated_at else None,
        }
