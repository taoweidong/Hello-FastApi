"""应用层 - 角色服务。"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.role_dto import RoleCreateDTO, RoleListQueryDTO, RoleResponseDTO, RoleUpdateDTO
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.infrastructure.database.models import Role


class RoleService:
    """角色操作的应用服务。"""

    def __init__(self, session: AsyncSession, role_repo: RoleRepositoryInterface):
        """初始化角色服务。

        Args:
            session: 数据库会话，用于事务控制
            role_repo: 角色仓储接口实例
        """
        self.session = session
        self.role_repo = role_repo

    async def create_role(self, dto: RoleCreateDTO) -> RoleResponseDTO:
        """创建新角色，可选分配权限。"""
        # 检查角色名称是否已存在
        if await self.role_repo.get_by_name(dto.name):
            raise ConflictError(f"角色名称 '{dto.name}' 已存在")
        # 检查角色编码是否已存在
        if await self.role_repo.get_by_code(dto.code):
            raise ConflictError(f"角色编码 '{dto.code}' 已存在")

        role = Role(
            name=dto.name,
            code=dto.code,
            description=dto.remark,  # 映射 remark 到 description
            status=dto.status,
        )
        await self.role_repo.create(role)
        await self.session.flush()
        # 重新获取以获得完整数据
        created_role = await self.role_repo.get_by_code(dto.code)
        if created_role is None:
            raise NotFoundError(f"角色 '{dto.name}' 创建失败")

        # 如果提供了权限ID列表，则分配权限
        if dto.permissionIds:
            await self.role_repo.assign_permissions_to_role(created_role.id, dto.permissionIds)

        return await self._role_to_response(created_role)

    async def get_role(self, role_id: str) -> RoleResponseDTO:
        """根据 ID 获取角色详情（含权限列表）。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"角色ID '{role_id}' 不存在")
        return await self._role_to_response(role)

    async def get_roles(self, query: RoleListQueryDTO) -> tuple[list[RoleResponseDTO], int]:
        """获取角色列表（分页）。"""
        # 获取总数
        total = await self.role_repo.count(
            role_name=query.name,  # 前端使用 name 字段
            status=query.status,
        )
        # 获取列表
        roles = await self.role_repo.get_all(
            page_num=query.pageNum,
            page_size=query.pageSize,
            role_name=query.name,  # 前端使用 name 字段
            status=query.status,
        )
        # 转换为响应DTO
        role_responses = []
        for role in roles:
            response = await self._role_to_response(role)
            role_responses.append(response)
        return role_responses, total

    async def update_role(self, role_id: str, dto: RoleUpdateDTO) -> RoleResponseDTO:
        """更新角色信息和权限。"""
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"角色ID '{role_id}' 不存在")

        # 更新名称（如果提供）
        if dto.name is not None:
            existing = await self.role_repo.get_by_name(dto.name)
            if existing and existing.id != role_id:
                raise ConflictError(f"角色名称 '{dto.name}' 已存在")
            role.name = dto.name

        # 更新编码（如果提供）
        if dto.code is not None:
            existing = await self.role_repo.get_by_code(dto.code)
            if existing and existing.id != role_id:
                raise ConflictError(f"角色编码 '{dto.code}' 已存在")
            role.code = dto.code

        # 更新备注（如果提供）
        if dto.remark is not None:
            role.description = dto.remark

        # 更新状态（如果提供）
        if dto.status is not None:
            role.status = dto.status

        await self.role_repo.update(role)
        await self.session.flush()

        # 如果提供了权限ID列表，则重新分配权限
        if dto.permissionIds is not None:
            await self.role_repo.assign_permissions_to_role(role_id, dto.permissionIds)

        # 重新获取以加载关系
        updated_role = await self.role_repo.get_by_id(role_id)
        if updated_role is None:
            raise NotFoundError(f"角色ID '{role_id}' 不存在")
        return await self._role_to_response(updated_role)

    async def delete_role(self, role_id: str) -> bool:
        """删除角色。"""
        if not await self.role_repo.delete(role_id):
            raise NotFoundError(f"角色ID '{role_id}' 不存在")
        return True

    async def assign_permissions(self, role_id: str, permission_ids: list[str]) -> bool:
        """为角色分配权限。"""
        # 检查角色是否存在
        role = await self.role_repo.get_by_id(role_id)
        if role is None:
            raise NotFoundError(f"角色ID '{role_id}' 不存在")

        await self.role_repo.assign_permissions_to_role(role_id, permission_ids)
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
        # 获取角色的权限列表
        permissions = await self.role_repo.get_role_permissions(role.id)
        perm_list = [{"id": p.id, "code": p.code} for p in permissions] if permissions else []

        return RoleResponseDTO(
            id=role.id,
            name=role.name,
            code=role.code,
            remark=role.description,  # 映射 description 到 remark
            status=role.status,
            permissions=perm_list,
            createTime=role.created_at,
            updateTime=role.updated_at,
        )
