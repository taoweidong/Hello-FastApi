"""字典应用服务工厂测试。"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetDictionaryService:
    """get_dictionary_service 函数测试。"""

    @patch("src.api.dependencies.dictionary_service.DictionaryRepository")
    async def test_returns_dictionary_service(self, mock_dict_repo):
        """应返回配置好的 DictionaryService 实例。"""
        mock_repo_instance = MagicMock()
        mock_dict_repo.return_value = mock_repo_instance

        from src.api.dependencies.dictionary_service import get_dictionary_service

        mock_db = MagicMock()
        service = await get_dictionary_service(db=mock_db)
        from src.application.services.dictionary_service import DictionaryService
        assert isinstance(service, DictionaryService)
        assert service.dict_repo == mock_repo_instance
        mock_dict_repo.assert_called_once_with(mock_db)
