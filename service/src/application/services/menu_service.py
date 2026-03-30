"""应用层 - 菜单服务。

提供菜单相关的业务逻辑，包括菜单树构建、用户菜单过滤等。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.menu_dto import MenuCreateDTO, MenuUpdateDTO
from src.core.exceptions import ConflictError, NotFoundError
from src.infrastructure.database.models import Menu
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.rbac_repository import PermissionRepository


class MenuService:
    """菜单领域操作的应用服务。"""

    def __init__(self, session: AsyncSession):
        """初始化菜单服务。

        Args:
            session: 数据库会话
        """
        self.session = session
        self.menu_repo = MenuRepository()
        self.perm_repo: PermissionRepository | None = None

    def _get_perm_repo(self) -> PermissionRepository:
        """获取权限仓储实例（懒加载）。"""
        if self.perm_repo is None:
            self.perm_repo = PermissionRepository(self.session)
        return self.perm_repo

    async def get_menu_tree(self, session: AsyncSession) -> list[dict]:
        """获取完整菜单树。"""
        all_menus = await self.menu_repo.get_all(session)
        return self._build_tree(all_menus, None)

    async def get_user_menus(self, user_id: str, session: AsyncSession) -> list[dict]:
        """获取用户可访问的菜单（根据用户权限过滤）。

        超级用户返回所有菜单，普通用户根据权限过滤。
        """
        # 获取所有菜单
        all_menus = await self.menu_repo.get_all(session)

        # 获取用户的所有权限编码
        perm_repo = self._get_perm_repo()
        user_permissions = await perm_repo.get_user_permissions(user_id)
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

    async def create_menu(self, dto: MenuCreateDTO, session: AsyncSession) -> dict:
        """创建菜单。"""
        # 如果有父菜单，验证父菜单是否存在
        if dto.parentId:
            parent = await self.menu_repo.get_by_id(dto.parentId, session)
            if not parent:
                raise NotFoundError("父菜单不存在")

        menu = Menu(
            name=dto.name,
            path=dto.path,
            component=dto.component,
            icon=dto.icon,
            title=dto.title,
            show_link=dto.showLink,
            parent_id=dto.parentId,
            order_num=dto.order,
            permissions=",".join(dto.permissions) if dto.permissions else None,
            status=1,
        )
        menu = await self.menu_repo.create(menu, session)
        return self._to_response(menu)

    async def update_menu(self, menu_id: str, dto: MenuUpdateDTO, session: AsyncSession) -> dict:
        """更新菜单。"""
        menu = await self.menu_repo.get_by_id(menu_id, session)
        if not menu:
            raise NotFoundError("菜单不存在")

        # 检查是否将菜单设置为自己的子菜单（循环引用）
        if dto.parentId == menu_id:
            raise ConflictError("不能将菜单设置为自己的子菜单")

        # 如果有父菜单，验证父菜单是否存在
        if dto.parentId:
            parent = await self.menu_repo.get_by_id(dto.parentId, session)
            if not parent:
                raise NotFoundError("父菜单不存在")
            # 检查是否将菜单设置为其子菜单的子菜单（避免循环）
            if await self._is_descendant(menu_id, dto.parentId, session):
                raise ConflictError("不能将菜单设置为其子菜单的子菜单")
            menu.parent_id = dto.parentId

        # 选择性更新非 None 字段
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
            menu.show_link = dto.showLink
        if dto.permissions is not None:
            menu.permissions = ",".join(dto.permissions) if dto.permissions else None
        if dto.order is not None:
            menu.order_num = dto.order

        menu = await self.menu_repo.update(menu, session)
        return self._to_response(menu)

    async def delete_menu(self, menu_id: str, session: AsyncSession) -> bool:
        """删除菜单。"""
        # 检查菜单是否存在
        menu = await self.menu_repo.get_by_id(menu_id, session)
        if not menu:
            raise NotFoundError("菜单不存在")

        # 检查是否有子菜单
        children = await self.menu_repo.get_by_parent_id(menu_id, session)
        if children:
            raise ConflictError("该菜单下有子菜单，请先删除子菜单")

        return await self.menu_repo.delete(menu_id, session)

    async def _is_descendant(self, ancestor_id: str, descendant_id: str, session: AsyncSession) -> bool:
        """检查 descendant_id 是否是 ancestor_id 的后代（用于防止循环引用）。"""
        children = await self.menu_repo.get_by_parent_id(descendant_id, session)
        for child in children:
            if child.id == ancestor_id:
                return True
            if await self._is_descendant(ancestor_id, child.id, session):
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
        """将 Menu 模型转为响应字典。"""
        return {
            "id": menu.id,
            "name": menu.name,
            "path": menu.path,
            "component": menu.component,
            "icon": menu.icon,
            "title": menu.title,
            "showLink": menu.show_link,
            "parentId": menu.parent_id,
            "permissions": menu.permissions.split(",") if menu.permissions else [],
            "order": menu.order_num,
            "status": menu.status,
            "children": [],
            "createTime": menu.created_at.isoformat() if menu.created_at else None,
            "updateTime": menu.updated_at.isoformat() if menu.updated_at else None,
        }
