"""部门应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.department_service import DepartmentService


async def get_department_service(repos: RepoBundle = Depends(get_repositories)) -> DepartmentService:
    """获取部门服务实例。

    注入部门仓储依赖（仓储来自请求级仓储束，事务约定见 repositories.py）。
    """
    return DepartmentService(dept_repo=repos.department)
