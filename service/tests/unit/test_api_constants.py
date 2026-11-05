import pytest

from src.api.constants import API_PREFIX, API_SYSTEM_PREFIX


@pytest.mark.unit
class TestAPIConstants:
    def test_api_prefix(self):
        assert API_PREFIX == "/api"

    def test_system_prefix(self):
        assert API_SYSTEM_PREFIX == "/api/system"
