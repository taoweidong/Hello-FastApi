"""应用层 - 部门服务。

提供部门相关的业务逻辑，包括部门的增删改查等操作。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.department_dto import DepartmentCreateDTO, DepartmentListQueryDTO, DepartmentResponseDTO, DepartmentUpdateDTO
from src.domain.exceptions import BusinessError, ConflictError, NotFoundError
from src.domain.repositories.department_repository import DepartmentRepositoryInterface
from src.infrastructure.database.models import Department


class DepartmentService:
    """部门领域操作的应用服务。"""

    def __init__(self, session: AsyncSession, dept_repo: DepartmentRepositoryInterface):
        """初始化部门服务。

        Args:
            session: 数据库会话，用于事务控制
            dept_repo: 部门仓储接口实例
        """
        self.session = session
        self.dept_repo = dept_repo

    async def get_departments(self, query: DepartmentListQueryDTO) -> list[DepartmentResponseDTO]:
        """获取部门列表（扁平结构，前端自动转树）。

        Args:
            query: 查询参数

        Returns:
            部门列表
        """
        all_depts = await self.dept_repo.get_all(session=self.session)

        # 前端筛选
        filtered_depts = all_depts
        if query.name:
            filtered_depts = [d for d in filtered_depts if query.name in d.name]
        if query.isActive is not None:
            filtered_depts = [d for d in filtered_depts if d.is_active == query.isActive]

        return [self._to_response(d) for d in filtered_depts]

    async def create_department(self, dto: DepartmentCreateDTO) -> DepartmentResponseDTO:
        """创建部门。

        Args:
            dto: 创建请求

        Returns:
            创建的部门

        Raises:
            ConflictError: 部门名称已存在
        """
        # 检查名称唯一性
        existing = await self.dept_repo.get_by_name(dto.name, session=self.session)
        if existing:
            raise ConflictError("部门名称已存在")

        # 检查编码唯一性
        if dto.code:
            existing_code = await self.dept_repo.get_by_code(dto.code, session=self.session) if hasattr(self.dept_repo, "get_by_code") else None
            if existing_code:
                raise ConflictError("部门编码已存在")

        # 处理 parentId：前端传递的是 int，需要转换为字符串或 None
        parent_id = dto.parentId
        if parent_id:
            # 验证父部门是否存在
            parent = await self.dept_repo.get_by_id(parent_id, session=self.session)
            if not parent:
                raise BusinessError("父部门不存在")

        # 创建部门（新字段：mode_type/code/rank/auto_bind/is_active/description）
        department = Department(name=dto.name, parent_id=parent_id, mode_type=dto.modeType, code=dto.code, rank=dto.rank, auto_bind=dto.autoBind, is_active=dto.isActive, description=dto.description)

        await self.dept_repo.create(department, session=self.session)
        await self.session.flush()
        # 重新获取以确保返回完整模型
        created = await self.dept_repo.get_by_name(dto.name, session=self.session)
        if created is None:
            raise BusinessError("部门创建后无法加载")
        return self._to_response(created)

    async def update_department(self, dept_id: str, dto: DepartmentUpdateDTO) -> DepartmentResponseDTO:
        """更新部门。

        Args:
            dept_id: 部门ID
            dto: 更新请求

        Returns:
            更新后的部门

        Raises:
            NotFoundError: 部门不存在
            BusinessError: 不能将部门设为自己的子部门
        """
        department = await self.dept_repo.get_by_id(dept_id, session=self.session)
        if not department:
            raise NotFoundError("部门不存在")

        # 处理 parentId
        if dto.parentId is not None:
            if dto.parentId == dept_id:
                raise BusinessError("不能将部门设为自己的子部门")
            if dto.parentId:
                parent = await self.dept_repo.get_by_id(dto.parentId, session=self.session)
                if not parent:
                    raise BusinessError("父部门不存在")
            department.parent_id = dto.parentId or None

        # 更新字段（新字段映射）
        if dto.name is not None:
            department.name = dto.name
        if dto.modeType is not None:
            department.mode_type = dto.modeType
        if dto.code is not None:
            department.code = dto.code
        if dto.rank is not None:
            department.rank = dto.rank
        if dto.autoBind is not None:
            department.auto_bind = dto.autoBind
        if dto.isActive is not None:
            department.is_active = dto.isActive
        if dto.description is not None:
            department.description = dto.description

        await self.dept_repo.update(department, session=self.session)
        await self.session.flush()
        # 重新获取以确保返回完整模型
        updated = await self.dept_repo.get_by_id(dept_id, session=self.session)
        if updated is None:
            raise NotFoundError("部门不存在")
        return self._to_response(updated)

    async def delete_department(self, dept_id: str) -> bool:
        """删除部门。

        Args:
            dept_id: 部门ID

        Returns:
            是否删除成功

        Raises:
            NotFoundError: 部门不存在
            BusinessError: 部门下存在子部门
        """
        department = await self.dept_repo.get_by_id(dept_id, session=self.session)
        if not department:
            raise NotFoundError("部门不存在")

        # 检查是否有子部门
        children = await self.dept_repo.get_by_parent_id(dept_id, session=self.session)
        if children:
            raise BusinessError("部门下存在子部门，不能删除")

        success = await self.dept_repo.delete(dept_id, session=self.session)
        await self.session.flush()
        return success

    @staticmethod
    def _to_response(dept: Department) -> DepartmentResponseDTO:
        """将 Department 模型转换为响应 DTO。"""
        return DepartmentResponseDTO(
            id=dept.id, parentId=dept.parent_id, name=dept.name, modeType=dept.mode_type, code=dept.code, rank=dept.rank, autoBind=dept.auto_bind, isActive=dept.is_active, creatorId=dept.creator_id, modifierId=dept.modifier_id, createdTime=dept.created_time, updatedTime=dept.updated_time, description=dept.description
        )
