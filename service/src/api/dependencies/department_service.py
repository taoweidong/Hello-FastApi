"""部门应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.department_service import DepartmentService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.department_repository import DepartmentRepository


async def get_department_service(db: AsyncSession = Depends(get_db)) -> DepartmentService:
    """获取部门服务实例。

    注入部门仓储依赖。
    """
    dept_repo = DepartmentRepository(db)
    return DepartmentService(dept_repo=dept_repo)
