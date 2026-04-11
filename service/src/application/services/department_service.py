"""应用层 - 部门服务。

提供部门相关的业务逻辑，包括部门的增删改查等操作。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.department_dto import DepartmentCreateDTO, DepartmentListQueryDTO, DepartmentUpdateDTO
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

    async def get_departments(self, query: DepartmentListQueryDTO) -> list[Department]:
        """获取部门列表（扁平结构，前端自动转树）。

        Args:
            query: 查询参数

        Returns:
            部门列表
        """
        all_depts = await self.dept_repo.get_all(self.session)

        # 前端筛选
        filtered_depts = all_depts
        if query.name:
            filtered_depts = [d for d in filtered_depts if query.name in d.name]
        if query.status is not None:
            filtered_depts = [d for d in filtered_depts if d.status == query.status]

        return filtered_depts

    async def create_department(self, dto: DepartmentCreateDTO) -> Department:
        """创建部门。

        Args:
            dto: 创建请求

        Returns:
            创建的部门

        Raises:
            ConflictError: 部门名称已存在
        """
        # 检查名称唯一性
        existing = await self.dept_repo.get_by_name(dto.name, self.session)
        if existing:
            raise ConflictError("部门名称已存在")

        # 处理 parentId：前端传递的是 int，需要转换为字符串或 None
        parent_id = None
        if dto.parentId and dto.parentId != 0:
            # 验证父部门是否存在
            parent = await self.dept_repo.get_by_id(str(dto.parentId), self.session)
            if not parent:
                raise BusinessError("父部门不存在")
            parent_id = str(dto.parentId)

        # 创建部门
        department = Department(name=dto.name, parent_id=parent_id, sort=dto.sort, principal=dto.principal, phone=dto.phone, email=dto.email, status=dto.status, remark=dto.remark)

        await self.dept_repo.create(department, self.session)
        await self.session.flush()
        # 重新获取以确保返回完整模型
        created = await self.dept_repo.get_by_name(dto.name, self.session)
        await self.session.commit()
        if created is None:
            raise BusinessError("部门创建后无法加载")
        return created

    async def update_department(self, dept_id: str, dto: DepartmentUpdateDTO) -> Department:
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
        department = await self.dept_repo.get_by_id(dept_id, self.session)
        if not department:
            raise NotFoundError("部门不存在")

        # 更新字段
        update_data = dto.model_dump(exclude_unset=True, exclude={"parentId"})

        # 处理 parentId
        if dto.parentId is not None:
            if dto.parentId == 0:
                department.parent_id = None
            else:
                # 验证不能将部门设为自己的子部门
                if str(dto.parentId) == dept_id:
                    raise BusinessError("不能将部门设为自己的子部门")

                parent = await self.dept_repo.get_by_id(str(dto.parentId), self.session)
                if not parent:
                    raise BusinessError("父部门不存在")
                department.parent_id = str(dto.parentId)

        for key, value in update_data.items():
            setattr(department, key, value)

        await self.dept_repo.update(department, self.session)
        await self.session.flush()
        # 重新获取以确保返回完整模型
        updated = await self.dept_repo.get_by_id(dept_id, self.session)
        await self.session.commit()
        if updated is None:
            raise NotFoundError("部门不存在")
        return updated

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
        department = await self.dept_repo.get_by_id(dept_id, self.session)
        if not department:
            raise NotFoundError("部门不存在")

        # 检查是否有子部门
        children = await self.dept_repo.get_by_parent_id(dept_id, self.session)
        if children:
            raise BusinessError("部门下存在子部门，不能删除")

        # 检查是否有关联用户（需要查询用户表，暂时跳过，前端已做限制）

        success = await self.dept_repo.delete(dept_id, self.session)
        await self.session.commit()
        return success
