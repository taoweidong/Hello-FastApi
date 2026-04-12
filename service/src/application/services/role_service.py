"""应用层 - 角色服务。"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.role_dto import RoleCreateDTO, RoleListQueryDTO, RoleResponseDTO, RoleUpdateDTO
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.infrastructure.database.models import Role


class RoleService:
    """角色操作的应用服务。"""

    def __init__(self, session: AsyncSession, role_repo: RoleRepositoryInterface):
        self.session = session
        self.role_repo = role_repo

    async def create_role(self, dto: RoleCreateDTO) -> RoleResponseDTO:
        """创建新角色，可选分配菜单。"""
        if await self.role_repo.get_by_name(dto.name):
            raise ConflictError(f"角色名称 '{dto.name}' 已存在")
        if await self.role_repo.get_by_code(dto.code):
            raise ConflictError(f"角色编码 '{dto.code}' 已存在")

        role = Role(name=dto.name, code=dto.code, description=dto.description, is_active=dto.isActive if dto.isActive is not None else 1)
        await self.role_repo.create(role)
        await self.session.flush()
        created_role = await self.role_repo.get_by_code(dto.code)
        if created_role is None:
            raise NotFoundError(f"角色 '{dto.name}' 创建失败")

        # 如果提供了菜单ID列表，则分配菜单
        if dto.menuIds:
            await self.role_repo.assign_menus_to_role(created_role.id, dto.menuIds)

        return await self._role_to_response(created_role)

    async def get_role(self, role_id: str) -> RoleResponseDTO:
        """根据 ID 获取角色详情。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"角色ID '{role_id}' 不存在")
        return await self._role_to_response(role)

    async def get_roles(self, query: RoleListQueryDTO) -> tuple[list[RoleResponseDTO], int]:
        """获取角色列表（分页）。"""
        total = await self.role_repo.count(role_name=query.name, is_active=query.isActive)
        roles = await self.role_repo.get_all(page_num=query.pageNum, page_size=query.pageSize, role_name=query.name, is_active=query.isActive)
        role_responses = [await self._role_to_response(r) for r in roles]
        return role_responses, total

    async def update_role(self, role_id: str, dto: RoleUpdateDTO) -> RoleResponseDTO:
        """更新角色信息和菜单。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"角色ID '{role_id}' 不存在")

        if dto.name is not None:
            existing = await self.role_repo.get_by_name(dto.name)
            if existing and existing.id != role_id:
                raise ConflictError(f"角色名称 '{dto.name}' 已存在")
            role.name = dto.name

        if dto.code is not None:
            existing = await self.role_repo.get_by_code(dto.code)
            if existing and existing.id != role_id:
                raise ConflictError(f"角色编码 '{dto.code}' 已存在")
            role.code = dto.code

        if dto.description is not None:
            role.description = dto.description

        if dto.isActive is not None:
            role.is_active = dto.isActive

        await self.role_repo.update(role)
        await self.session.flush()

        # 如果提供了菜单ID列表，则重新分配菜单
        if dto.menuIds is not None:
            await self.role_repo.assign_menus_to_role(role_id, dto.menuIds)

        updated_role = await self.role_repo.get_by_id(role_id)
        if updated_role is None:
            raise NotFoundError(f"角色ID '{role_id}' 不存在")
        return await self._role_to_response(updated_role)

    async def delete_role(self, role_id: str) -> bool:
        """删除角色。"""
        if not await self.role_repo.delete(role_id):
            raise NotFoundError(f"角色ID '{role_id}' 不存在")
        return True

    async def assign_menus(self, role_id: str, menu_ids: list[str]) -> bool:
        """为角色分配菜单权限。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"角色ID '{role_id}' 不存在")

        await self.role_repo.assign_menus_to_role(role_id, menu_ids)
        return True

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """为用户分配角色。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"角色 ID '{role_id}' 不存在")

        if not await self.role_repo.assign_role_to_user(user_id, role_id):
            raise ConflictError("角色已分配给该用户")
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """移除用户的角色。"""
        if not await self.role_repo.remove_role_from_user(user_id, role_id):
            raise NotFoundError("角色分配关系不存在")
        return True

    async def get_user_roles(self, user_id: str) -> list[RoleResponseDTO]:
        """获取用户的所有角色。"""
        roles = await self.role_repo.get_user_roles(user_id)
        return [await self._role_to_response(r) for r in roles]

    async def _role_to_response(self, role: Role) -> RoleResponseDTO:
        """将Role模型转换为响应DTO。"""
        # 获取角色的菜单ID列表
        menu_ids = await self.role_repo.get_role_menu_ids(role.id)
        menu_list = [{"id": mid} for mid in menu_ids] if menu_ids else []

        return RoleResponseDTO(id=role.id, name=role.name, code=role.code, isActive=role.is_active, menus=menu_list, creatorId=role.creator_id, modifierId=role.modifier_id, createdTime=role.created_time, updatedTime=role.updated_time, description=role.description)
