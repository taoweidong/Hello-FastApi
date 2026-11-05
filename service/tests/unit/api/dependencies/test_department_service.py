"""部门应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetDepartmentService:
    """get_department_service 函数测试。"""

    async def test_returns_department_service(self):
        """应返回配置好的 DepartmentService，部门仓储取自请求级仓储束。"""
        from src.api.dependencies.department_service import get_department_service
        from src.api.dependencies.repositories import RepoBundle
        from src.application.services.department_service import DepartmentService

        repos = RepoBundle(MagicMock())
        service = await get_department_service(repos=repos)

        assert isinstance(service, DepartmentService)
        assert service.dept_repo is repos.department
