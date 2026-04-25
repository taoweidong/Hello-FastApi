import pytest

from src.api.constants import API_PREFIX, API_SYSTEM_PREFIX, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


@pytest.mark.unit
class TestAPIConstants:
    def test_api_prefix(self):
        assert API_PREFIX == "/api"

    def test_system_prefix(self):
        assert API_SYSTEM_PREFIX == "/api/system"

    def test_default_page_size(self):
        assert DEFAULT_PAGE_SIZE == 20

    def test_max_page_size(self):
        assert MAX_PAGE_SIZE == 100
