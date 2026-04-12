"""菜单管理路由模块。

提供菜单的增删改查、菜单树获取、用户菜单获取等功能。
菜单结构: Menu + MenuMeta（一对一关联）。
menu_type: 0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限
使用 rank 字段排序（替代旧的 order_num）。
路由前缀: /api/system/menu
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends

from src.api.common import success_response
from src.api.dependencies import get_current_active_user, get_menu_service, require_permission
from src.application.dto.menu_dto import MenuCreateDTO, MenuUpdateDTO
from src.application.services.menu_service import MenuService


class MenuRouter(Routable):
    """菜单管理路由类，提供菜单增删改查、菜单树获取、用户菜单获取等功能。"""

    @post("")
    async def get_menu_list(self, menu_service: MenuService = Depends(get_menu_service), current_user: dict = Depends(require_permission("menu:view"))) -> dict:
        """获取菜单列表（扁平结构）。"""
        all_menus = await menu_service.menu_repo.get_all(menu_service.session)
        menu_list = [menu_service._to_response(menu) for menu in all_menus]
        return success_response(data=menu_list)

    @get("/tree")
    async def get_menu_tree(self, menu_service: MenuService = Depends(get_menu_service), current_user: dict = Depends(require_permission("menu:view"))) -> dict:
        """获取完整菜单树。"""
        tree = await menu_service.get_menu_tree()
        return success_response(data=tree)

    @get("/user-menus")
    async def get_user_menus(self, menu_service: MenuService = Depends(get_menu_service), current_user: dict = Depends(get_current_active_user)) -> dict:
        """获取当前用户可访问的菜单。"""
        menus = await menu_service.get_user_menus(current_user["id"])
        return success_response(data=menus)

    @post("/create")
    async def create_menu(self, dto: MenuCreateDTO, menu_service: MenuService = Depends(get_menu_service), current_user: dict = Depends(require_permission("menu:add"))) -> dict:
        """创建菜单（含元数据）。"""
        menu = await menu_service.create_menu(dto)
        return success_response(data=menu, code=201, message="创建成功")

    @put("/{menu_id}")
    async def update_menu(self, menu_id: str, dto: MenuUpdateDTO, menu_service: MenuService = Depends(get_menu_service), current_user: dict = Depends(require_permission("menu:edit"))) -> dict:
        """更新菜单（含元数据）。"""
        menu = await menu_service.update_menu(menu_id, dto)
        return success_response(data=menu, message="更新成功")

    @delete("/{menu_id}")
    async def delete_menu(self, menu_id: str, menu_service: MenuService = Depends(get_menu_service), current_user: dict = Depends(require_permission("menu:delete"))) -> dict:
        """删除菜单。"""
        await menu_service.delete_menu(menu_id)
        return success_response(message="删除成功")