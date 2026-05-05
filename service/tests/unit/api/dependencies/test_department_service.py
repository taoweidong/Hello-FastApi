"""部门应用服务工厂测试。"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetDepartmentService:
    """get_department_service 函数测试。"""

    @patch("src.api.dependencies.department_service.DepartmentRepository")
    async def test_returns_department_service(self, mock_dept_repo):
        """应返回配置好的 DepartmentService 实例。"""
        mock_repo_instance = MagicMock()
        mock_dept_repo.return_value = mock_repo_instance

        from src.api.dependencies.department_service import get_department_service

        mock_db = MagicMock()
        service = await get_department_service(db=mock_db)
        from src.application.services.department_service import DepartmentService
        assert isinstance(service, DepartmentService)
        assert service.dept_repo == mock_repo_instance
        mock_dept_repo.assert_called_once_with(mock_db)
