"""应用层 - 部门服务。

提供部门相关的业务逻辑，包括部门的增删改查等操作。
"""

from src.application.dto.department_dto import (
    DepartmentCreateDTO,
    DepartmentListQueryDTO,
    DepartmentResponseDTO,
    DepartmentUpdateDTO,
)
from src.domain.entities.department import DepartmentEntity
from src.domain.exceptions import BusinessError, ConflictError, NotFoundError
from src.domain.repositories.department_repository import DepartmentRepositoryInterface


class DepartmentService:
    """部门领域操作的应用服务。"""

    def __init__(self, dept_repo: DepartmentRepositoryInterface):
        self.dept_repo = dept_repo

    async def get_departments(self, query: DepartmentListQueryDTO) -> list[DepartmentResponseDTO]:
        """获取部门列表（数据库级别过滤，扁平结构，前端自动转树）。"""
        departments = await self.dept_repo.get_filtered(name=query.name, is_active=query.isActive)
        return [self._to_response(d) for d in departments]

    async def get_dept_tree(self) -> list[dict]:
        """获取部门树形结构。"""
        all_depts = await self.dept_repo.get_all()
        return self._build_tree(all_depts, None)

    def _build_tree(self, depts: list[DepartmentEntity], parent_id: str | None) -> list[dict]:
        """构建部门树形结构。"""
        tree = []
        for dept in depts:
            if dept.parent_id == parent_id:
                node = {
                    "id": dept.id,
                    "parentId": dept.parent_id,
                    "name": dept.name,
                    "code": dept.code,
                    "rank": dept.rank,
                    "isActive": dept.is_active,
                }
                children = self._build_tree(depts, dept.id)
                if children:
                    node["children"] = children
                tree.append(node)
        return sorted(tree, key=lambda x: x.get("rank", 0))

    async def create_department(self, dto: DepartmentCreateDTO) -> DepartmentResponseDTO:
        """创建部门。"""
        # 检查名称唯一性
        existing = await self.dept_repo.get_by_name(dto.name)
        if existing:
            raise ConflictError("部门名称已存在")

        # 检查编码唯一性
        if dto.code:
            existing_code = await self.dept_repo.get_by_code(dto.code)
            if existing_code:
                raise ConflictError("部门编码已存在")

        # 处理 parentId
        parent_id = dto.parentId
        if parent_id:
            parent = await self.dept_repo.get_by_id(parent_id)
            if not parent:
                raise BusinessError("父部门不存在")

        # 创建部门
        department = DepartmentEntity.create_new(
            name=dto.name,
            code=dto.code,
            parent_id=parent_id,
            mode_type=dto.modeType,
            rank=dto.rank,
            auto_bind=dto.autoBind,
            description=dto.description,
        )
        department.is_active = dto.isActive

        created = await self.dept_repo.create(department)
        return self._to_response(created)

    async def update_department(self, dept_id: str, dto: DepartmentUpdateDTO) -> DepartmentResponseDTO:
        """更新部门。"""
        department = await self.dept_repo.get_by_id(dept_id)
        if not department:
            raise NotFoundError("部门不存在")

        # 处理 parentId
        if dto.parentId is not None:
            if department.is_circular_reference(dto.parentId):
                raise BusinessError("不能将部门设为自己的子部门")
            if dto.parentId:
                parent = await self.dept_repo.get_by_id(dto.parentId)
                if not parent:
                    raise BusinessError("父部门不存在")
            department.parent_id = dto.parentId or None

        department.update_info(
            name=dto.name,
            code=dto.code,
            mode_type=dto.modeType,
            rank=dto.rank,
            auto_bind=dto.autoBind,
            description=dto.description,
        )
        if dto.isActive is not None:
            department.is_active = dto.isActive

        updated = await self.dept_repo.update(department)
        return self._to_response(updated)

    async def delete_department(self, dept_id: str) -> bool:
        """删除部门。"""
        department = await self.dept_repo.get_by_id(dept_id)
        if not department:
            raise NotFoundError("部门不存在")

        # 检查是否有子部门
        children = await self.dept_repo.get_by_parent_id(dept_id)
        if children:
            raise BusinessError("部门下存在子部门，不能删除")

        return await self.dept_repo.delete(dept_id)

    @staticmethod
    def _to_response(dept: DepartmentEntity) -> DepartmentResponseDTO:
        """将部门实体转换为响应 DTO。"""
        return DepartmentResponseDTO(
            id=dept.id,
            parentId=dept.parent_id,
            name=dept.name,
            modeType=dept.mode_type,
            code=dept.code,
            rank=dept.rank,
            autoBind=dept.auto_bind,
            isActive=dept.is_active,
            creatorId=dept.creator_id,
            modifierId=dept.modifier_id,
            createdTime=dept.created_time,
            updatedTime=dept.updated_time,
            description=dept.description,
        )
