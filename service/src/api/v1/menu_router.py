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
from src.api.common.response_schemas import ApiResponse
from src.api.dependencies import get_current_active_user, get_menu_service, require_permission
from src.application.dto.menu_dto import MenuCreateDTO, MenuStatusUpdateDTO, MenuUpdateDTO
from src.application.services.menu_service import MenuService
from src.domain.entities.user import UserEntity


class MenuRouter(Routable):
    """菜单管理路由类，提供菜单增删改查、菜单树获取、用户菜单获取等功能。"""

    @post("", response_model=ApiResponse[list[dict]])
    async def get_menu_list(
        self,
        menu_service: MenuService = Depends(get_menu_service),
        current_user: UserEntity = Depends(require_permission("menu:view")),
    ) -> dict:
        """获取菜单列表（扁平结构）。"""
        menu_list = await menu_service.get_menu_list()
        return success_response(data=menu_list)

    @get("/tree", response_model=ApiResponse[list[dict]])
    async def get_menu_tree(
        self,
        menu_service: MenuService = Depends(get_menu_service),
        current_user: UserEntity = Depends(require_permission("menu:view")),
    ) -> dict:
        """获取完整菜单树。"""
        tree = await menu_service.get_menu_tree()
        return success_response(data=tree)

    @get("/user-menus", response_model=ApiResponse[list[dict]])
    async def get_user_menus(
        self,
        menu_service: MenuService = Depends(get_menu_service),
        current_user: UserEntity = Depends(get_current_active_user),
    ) -> dict:
        """获取当前用户可访问的菜单（超管返回全部，普通用户按角色过滤）。"""
        menus = await menu_service.get_user_menus(current_user.id, is_superuser=current_user.is_superuser_user)
        return success_response(data=menus)

    @post("/create", response_model=ApiResponse[dict])
    async def create_menu(
        self,
        dto: MenuCreateDTO,
        menu_service: MenuService = Depends(get_menu_service),
        current_user: UserEntity = Depends(require_permission("menu:add")),
    ) -> dict:
        """创建菜单（含元数据）。"""
        menu = await menu_service.create_menu(dto)
        return success_response(data=menu.model_dump(), code=201, message="创建成功")

    @put("/{menu_id}", response_model=ApiResponse[dict])
    async def update_menu(
        self,
        menu_id: str,
        dto: MenuUpdateDTO,
        menu_service: MenuService = Depends(get_menu_service),
        current_user: UserEntity = Depends(require_permission("menu:edit")),
    ) -> dict:
        """更新菜单（含元数据）。"""
        menu = await menu_service.update_menu(menu_id, dto)
        return success_response(data=menu.model_dump(), message="更新成功")

    @put("/{menu_id}/status", response_model=ApiResponse[dict])
    async def update_menu_status(
        self,
        menu_id: str,
        dto: MenuStatusUpdateDTO,
        menu_service: MenuService = Depends(get_menu_service),
        current_user: UserEntity = Depends(require_permission("menu:edit")),
    ) -> dict:
        """更新菜单启用状态（前端菜单管理页的启用开关）。"""
        menu = await menu_service.update_menu(menu_id, MenuUpdateDTO(isActive=dto.isActive))
        return success_response(data=menu.model_dump(), message="状态更新成功")

    @delete("/{menu_id}", response_model=ApiResponse[None])
    async def delete_menu(
        self,
        menu_id: str,
        menu_service: MenuService = Depends(get_menu_service),
        current_user: UserEntity = Depends(require_permission("menu:delete")),
    ) -> dict:
        """删除菜单。"""
        await menu_service.delete_menu(menu_id)
        return success_response(message="删除成功")
