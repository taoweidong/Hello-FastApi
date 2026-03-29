"""菜单管理路由。

提供菜单的增删改查、菜单树获取、用户菜单获取等功能。
路由前缀: /api/system/menu
"""

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import success_response
from src.api.dependencies import get_current_active_user, require_permission
from src.application.dto.menu_dto import MenuCreateDTO, MenuUpdateDTO
from src.application.services.menu_service import MenuService
from src.infrastructure.database.connection import get_db
from src.infrastructure.repositories.menu_repository import MenuRepository

menu_router = APIRouter()
menu_service = MenuService()


@menu_router.post("")
async def get_menu_list(
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("menu:view")),
):
    """获取菜单列表（扁平结构）。
    
    前端调用: POST /api/system/menu
    返回扁平列表格式（非树形），符合 Pure Admin 前端标准。
    """
    menu_repo = MenuRepository()
    all_menus = await menu_repo.get_all(session)
    
    # 转换为前端期望的扁平列表格式
    menu_list = []
    for menu in all_menus:
        menu_dict = {
            "parentId": int(menu.parent_id) if menu.parent_id else 0,
            "id": int(menu.id) if menu.id.isdigit() else menu.id,
            "menuType": 0,  # 0-菜单, 1-iframe, 2-外链, 3-按钮
            "title": menu.title or menu.name,
            "name": menu.name,
            "path": menu.path or "",
            "component": menu.component or "",
            "rank": menu.order_num,
            "redirect": "",
            "icon": menu.icon or "",
            "extraIcon": "",
            "enterTransition": "",
            "leaveTransition": "",
            "activePath": "",
            "auths": menu.permissions or "",
            "frameSrc": "",
            "frameLoading": True,
            "keepAlive": False,
            "hiddenTag": False,
            "fixedTag": False,
            "showLink": menu.show_link if menu.show_link is not None else True,
            "showParent": False,
        }
        menu_list.append(menu_dict)
    
    return success_response(data=menu_list)


@menu_router.get("/tree")
async def get_menu_tree(
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("menu:view")),
):
    """获取完整菜单树。"""
    tree = await menu_service.get_menu_tree(session)
    return success_response(data=tree)


@menu_router.get("/user-menus")
async def get_user_menus(
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user),
):
    """获取当前用户可访问的菜单。"""
    menus = await menu_service.get_user_menus(current_user["id"], session)
    return success_response(data=menus)


@menu_router.post("/create")
async def create_menu(
    dto: MenuCreateDTO,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("menu:add")),
):
    """创建菜单。
    
    前端调用: POST /api/system/menu/create
    """
    menu = await menu_service.create_menu(dto, session)
    return success_response(data=menu, code=201, message="创建成功")


@menu_router.put("/{menu_id}")
async def update_menu(
    menu_id: str,
    dto: MenuUpdateDTO,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("menu:edit")),
):
    """更新菜单。"""
    menu = await menu_service.update_menu(menu_id, dto, session)
    return success_response(data=menu, message="更新成功")


@menu_router.delete("/{menu_id}")
async def delete_menu(
    menu_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("menu:delete")),
):
    """删除菜单。"""
    await menu_service.delete_menu(menu_id, session)
    return success_response(message="删除成功")
