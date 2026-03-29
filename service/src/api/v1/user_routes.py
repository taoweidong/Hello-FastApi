"""System API - 用户管理路由模块。

提供用户管理相关的接口，包括用户增删改查、密码管理、状态管理等功能。
路由前缀: /api/system/user
"""

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.common import success_response, list_response
from src.api.dependencies import get_current_user_id, require_permission
from src.application.dto.user_dto import (
    AssignRoleDTO,
    BatchDeleteDTO,
    ChangePasswordDTO,
    ResetPasswordDTO,
    UpdateStatusDTO,
    UserCreateDTO,
    UserListQueryDTO,
    UserUpdateDTO,
)
from src.application.services.user_service import UserService
from src.infrastructure.database import get_db

router = APIRouter()


@router.post("")
async def get_user_list(
    query: UserListQueryDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:view")),
):
    """获取用户列表接口（支持筛选和分页）。

    需要 user:view 权限。
    前端调用: POST /api/system/user
    响应格式: { list, total, pageSize, currentPage }

    Args:
        query: 用户列表查询参数
        db: 数据库会话

    Returns:
        Pure Admin 标准分页响应格式的用户列表
    """
    service = UserService(db)
    users, total = await service.get_users(query)

    # 转换为前端期望的字段格式
    user_list = []
    for user in users:
        user_dict = user.model_dump()
        # 添加 dept 字段（前端期望的部门格式）
        user_dict["dept"] = {"id": user_dict.get("dept_id") or 0, "name": ""}
        # 处理可能为 null 的字段，转换为空字符串
        if user_dict.get("phone") is None:
            user_dict["phone"] = ""
        if user_dict.get("email") is None:
            user_dict["email"] = ""
        if user_dict.get("nickname") is None:
            user_dict["nickname"] = ""
        if user_dict.get("avatar") is None:
            user_dict["avatar"] = ""
        if user_dict.get("remark") is None:
            user_dict["remark"] = ""
        # 移除不需要的字段
        user_dict.pop("dept_id", None)
        user_list.append(user_dict)

    return list_response(
        list_data=user_list,
        total=total,
        page_size=query.pageSize,
        current_page=query.pageNum,
    )


@router.post("/create", status_code=201)
async def create_user(
    dto: UserCreateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:add")),
):
    """创建用户接口。

    需要 user:add 权限。
    前端调用: POST /api/system/user/create

    Args:
        dto: 用户创建数据
        db: 数据库会话

    Returns:
        统一格式的成功响应，包含创建的用户信息
    """
    service = UserService(db)
    user = await service.create_user(dto)
    return success_response(data=user, message="创建成功", code=201)


@router.get("/info")
async def get_current_user_info(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户信息接口。

    Args:
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        统一格式的成功响应，包含当前用户完整信息（含角色权限）
    """
    service = UserService(db)
    user = await service.get_user(user_id)
    return success_response(data=user)


@router.get("/{user_id}")
async def get_user_detail(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:view")),
):
    """获取用户详情接口。

    需要 user:view 权限。

    Args:
        user_id: 用户ID
        db: 数据库会话

    Returns:
        统一格式的成功响应，包含用户详情
    """
    service = UserService(db)
    user = await service.get_user(user_id)
    return success_response(data=user)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    dto: UserUpdateDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:edit")),
):
    """更新用户接口。

    需要 user:edit 权限。

    Args:
        user_id: 用户ID
        dto: 用户更新数据
        db: 数据库会话

    Returns:
        统一格式的成功响应，包含更新后的用户信息
    """
    service = UserService(db)
    user = await service.update_user(user_id, dto)
    return success_response(data=user, message="更新成功")


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:delete")),
):
    """删除用户接口。

    需要 user:delete 权限。

    Args:
        user_id: 用户ID
        db: 数据库会话

    Returns:
        统一格式的成功响应
    """
    service = UserService(db)
    await service.delete_user(user_id)
    return success_response(message="删除成功")


@router.post("/batch-delete")
async def batch_delete_users(
    dto: BatchDeleteDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:delete")),
):
    """批量删除用户接口。

    需要 user:delete 权限。

    Args:
        dto: 批量删除请求数据（包含用户ID列表）
        db: 数据库会话

    Returns:
        统一格式的成功响应，包含删除结果
    """
    service = UserService(db)
    result = await service.batch_delete_users(dto.ids)
    return success_response(data=result, message="批量删除成功")


@router.put("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    dto: ResetPasswordDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:edit")),
):
    """重置用户密码接口（管理员功能）。

    需要 user:edit 权限。

    Args:
        user_id: 用户ID
        dto: 重置密码请求数据
        db: 数据库会话

    Returns:
        统一格式的成功响应
    """
    service = UserService(db)
    await service.reset_password(user_id, dto.newPassword)
    return success_response(message="密码重置成功")


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: str,
    dto: UpdateStatusDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:edit")),
):
    """更改用户状态接口。

    需要 user:edit 权限。

    Args:
        user_id: 用户ID
        dto: 更新状态请求数据
        db: 数据库会话

    Returns:
        统一格式的成功响应
    """
    service = UserService(db)
    await service.update_status(user_id, dto.status)
    return success_response(message="状态更新成功")


@router.post("/change-password")
async def change_password(
    dto: ChangePasswordDTO,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户密码接口。

    Args:
        dto: 密码修改数据（oldPassword, newPassword）
        user_id: 当前用户ID
        db: 数据库会话

    Returns:
        统一格式的成功响应
    """
    service = UserService(db)
    await service.change_password(user_id, dto)
    return success_response(message="密码修改成功")


@router.post("/assign-role")
async def assign_role(
    dto: AssignRoleDTO,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_permission("user:edit")),
):
    """为用户分配角色接口。

    需要 user:edit 权限。
    前端调用: POST /api/system/user/assign-role

    Args:
        dto: 分配角色请求数据（userId, roleIds）
        db: 数据库会话

    Returns:
        统一格式的成功响应
    """
    service = UserService(db)
    await service.assign_roles(dto.userId, dto.roleIds)
    return success_response(message="角色分配成功")
