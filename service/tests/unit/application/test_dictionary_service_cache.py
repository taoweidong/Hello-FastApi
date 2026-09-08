"""字典服务缓存逻辑的单元测试。

覆盖 get_dict_items_by_type 的缓存命中/未命中/回填，
以及写操作（增删改）对根字典缓存的失效逻辑。
"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.dictionary_dto import DictionaryCreateDTO, DictionaryUpdateDTO
from src.application.services.dictionary_service import DictionaryService
from src.domain.entities.dictionary import DictionaryEntity


@pytest.mark.unit
class TestDictionaryServiceCache:
    """字典缓存读写与失效测试类。"""

    @pytest.fixture
    def mock_dict_repo(self):
        """创建模拟字典仓储。"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_by_name = AsyncMock(return_value=None)
        repo.get_by_parent_id = AsyncMock(return_value=[])
        repo.get_max_sort = AsyncMock(return_value=0)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_cache(self):
        """创建模拟缓存服务。"""
        cache = AsyncMock()
        cache.get_dict_items = AsyncMock(return_value=None)
        cache.set_dict_items = AsyncMock(return_value=True)
        cache.invalidate_dict = AsyncMock(return_value=True)
        return cache

    @pytest.fixture
    def dict_service(self, mock_dict_repo, mock_cache):
        """创建带缓存服务的字典服务实例。"""
        return DictionaryService(dict_repo=mock_dict_repo, cache_service=mock_cache)

    # ---- get_dict_items_by_type ----

    @pytest.mark.asyncio
    async def test_cache_hit_returns_directly(self, dict_service, mock_dict_repo, mock_cache):
        """缓存命中时直接返回，不查询数据库。"""
        mock_cache.get_dict_items = AsyncMock(return_value=[{"label": "男", "value": "1"}])

        result = await dict_service.get_dict_items_by_type("sys_gender")

        assert result == [{"label": "男", "value": "1"}]
        mock_dict_repo.get_by_name.assert_not_called()
        mock_cache.set_dict_items.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_queries_db_and_backfills(self, dict_service, mock_dict_repo, mock_cache):
        """缓存未命中时查库并回填缓存，仅返回启用项且按 sort 升序。"""
        root = DictionaryEntity(id="root1", name="sys_gender")
        children = [
            DictionaryEntity(id="c1", name="sys_gender_female", label="女", value="2", sort=2),
            DictionaryEntity(id="c2", name="sys_gender_male", label="男", value="1", sort=1),
            DictionaryEntity(id="c3", name="sys_gender_off", label="停用项", value="9", sort=3, is_active=0),
        ]
        mock_dict_repo.get_by_name = AsyncMock(return_value=root)
        mock_dict_repo.get_by_parent_id = AsyncMock(return_value=children)

        result = await dict_service.get_dict_items_by_type("sys_gender")

        assert result == [{"label": "男", "value": "1"}, {"label": "女", "value": "2"}]
        mock_cache.set_dict_items.assert_called_once_with("sys_gender", result)

    @pytest.mark.asyncio
    async def test_type_not_found_returns_empty_and_caches(self, dict_service, mock_dict_repo, mock_cache):
        """字典类型不存在时返回空列表，并回填空列表防穿透。"""
        mock_dict_repo.get_by_name = AsyncMock(return_value=None)

        result = await dict_service.get_dict_items_by_type("not_exist")

        assert result == []
        mock_cache.set_dict_items.assert_called_once_with("not_exist", [])

    @pytest.mark.asyncio
    async def test_without_cache_service_degrades(self, mock_dict_repo):
        """无缓存服务时降级为直接查库。"""
        root = DictionaryEntity(id="root1", name="sys_status")
        child = DictionaryEntity(id="c1", name="sys_status_on", label="启用", value="1", sort=1)
        mock_dict_repo.get_by_name = AsyncMock(return_value=root)
        mock_dict_repo.get_by_parent_id = AsyncMock(return_value=[child])
        service = DictionaryService(dict_repo=mock_dict_repo, cache_service=None)

        result = await service.get_dict_items_by_type("sys_status")

        assert result == [{"label": "启用", "value": "1"}]

    # ---- 写操作缓存失效 ----

    @pytest.mark.asyncio
    async def test_create_child_invalidates_root_cache(self, dict_service, mock_dict_repo, mock_cache):
        """新增子项后失效所属根字典缓存。"""
        created = DictionaryEntity(id="c1", name="sys_gender_male", parent_id="root1")
        root = DictionaryEntity(id="root1", name="sys_gender")
        mock_dict_repo.get_by_id = AsyncMock(return_value=root)
        mock_dict_repo.create = AsyncMock(return_value=created)

        dto = DictionaryCreateDTO(name="sys_gender_male", label="男", value="1", parentId="root1", isActive=1)
        await dict_service.create_dictionary(dto)

        mock_cache.invalidate_dict.assert_called_once_with("sys_gender")

    @pytest.mark.asyncio
    async def test_create_root_does_not_invalidate(self, dict_service, mock_dict_repo, mock_cache):
        """新增根字典不影响已有缓存，不触发失效。"""
        created = DictionaryEntity(id="root1", name="sys_new_type")
        mock_dict_repo.create = AsyncMock(return_value=created)

        dto = DictionaryCreateDTO(name="sys_new_type", label="新类型", value="v", isActive=1)
        await dict_service.create_dictionary(dto)

        mock_cache.invalidate_dict.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_child_invalidates_root_cache(self, dict_service, mock_dict_repo, mock_cache):
        """更新子项后失效所属根字典缓存。"""
        child = DictionaryEntity(id="c1", name="sys_gender_male", label="男", parent_id="root1")
        root = DictionaryEntity(id="root1", name="sys_gender")

        async def _get_by_id(node_id: str):
            return {"c1": child, "root1": root}.get(node_id)

        mock_dict_repo.get_by_id = AsyncMock(side_effect=_get_by_id)
        mock_dict_repo.update = AsyncMock(return_value=child)

        dto = DictionaryUpdateDTO(label="男性")
        await dict_service.update_dictionary("c1", dto)

        mock_cache.invalidate_dict.assert_called_once_with("sys_gender")

    @pytest.mark.asyncio
    async def test_update_root_rename_invalidates_both_names(self, dict_service, mock_dict_repo, mock_cache):
        """根字典改名时同时失效新旧两个名称的缓存。"""
        root = DictionaryEntity(id="root1", name="sys_gender")
        mock_dict_repo.get_by_id = AsyncMock(return_value=root)
        renamed = DictionaryEntity(id="root1", name="sys_sex")
        mock_dict_repo.update = AsyncMock(return_value=renamed)

        dto = DictionaryUpdateDTO(name="sys_sex")
        await dict_service.update_dictionary("root1", dto)

        invalidated = {c.args[0] for c in mock_cache.invalidate_dict.call_args_list}
        assert invalidated == {"sys_gender", "sys_sex"}

    @pytest.mark.asyncio
    async def test_delete_child_invalidates_root_cache(self, dict_service, mock_dict_repo, mock_cache):
        """删除子项后失效所属根字典缓存。"""
        child = DictionaryEntity(id="c1", name="sys_gender_male", parent_id="root1")
        root = DictionaryEntity(id="root1", name="sys_gender")
        mock_dict_repo.get_by_id = AsyncMock(return_value=root)

        async def _get_by_id(node_id: str):
            return {"c1": child, "root1": root}.get(node_id)

        mock_dict_repo.get_by_id = AsyncMock(side_effect=_get_by_id)
        mock_dict_repo.delete = AsyncMock(return_value=True)

        result = await dict_service.delete_dictionary("c1")

        assert result is True
        mock_cache.invalidate_dict.assert_called_once_with("sys_gender")

    # ---- _resolve_root_name ----

    @pytest.mark.asyncio
    async def test_resolve_root_name_traces_upward(self, dict_service, mock_dict_repo):
        """多层嵌套时沿父链追溯到根字典名称。"""
        root = DictionaryEntity(id="r", name="sys_root")
        mid = DictionaryEntity(id="m", name="sys_mid", parent_id="r")

        async def _get_by_id(node_id: str):
            return {"r": root, "m": mid}.get(node_id)

        mock_dict_repo.get_by_id = AsyncMock(side_effect=_get_by_id)

        result = await dict_service._resolve_root_name("sys_leaf", "m")

        assert result == "sys_root"

    @pytest.mark.asyncio
    async def test_resolve_root_name_returns_self_when_no_parent(self, dict_service, mock_dict_repo):
        """无父节点时返回自身名称。"""
        result = await dict_service._resolve_root_name("sys_root", None)

        assert result == "sys_root"
        mock_dict_repo.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_write_without_cache_service_no_error(self, mock_dict_repo):
        """无缓存服务时写操作不报错。"""
        child = DictionaryEntity(id="c1", name="leaf", parent_id="root1")
        root = DictionaryEntity(id="root1", name="sys_root")

        async def _get_by_id(node_id: str):
            return {"c1": child, "root1": root}.get(node_id)

        mock_dict_repo.get_by_id = AsyncMock(side_effect=_get_by_id)
        mock_dict_repo.delete = AsyncMock(return_value=True)
        service = DictionaryService(dict_repo=mock_dict_repo, cache_service=None)

        result = await service.delete_dictionary("c1")

        assert result is True
