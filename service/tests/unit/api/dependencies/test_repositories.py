"""请求级仓储束（RepoBundle / get_repositories）测试。

核心断言是事务约定的工具化保证：束内所有仓储共享同一个 Session，
且 infrastructure 层每新增一个仓储实现都必须出现在束里——否则服务工厂
只能自建 Session，请求级单事务静默分裂。
"""

import importlib
import inspect
import pkgutil
from unittest.mock import MagicMock

import pytest

from src.api.dependencies.repositories import RepoBundle, get_repositories


def _repository_classes() -> set[type]:
    """收集 infrastructure/repositories 包下定义的全部仓储实现类（不含基类）。"""
    import src.infrastructure.repositories as package

    classes: set[type] = set()
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name == "base":
            continue
        module = importlib.import_module(f"src.infrastructure.repositories.{module_info.name}")
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.endswith("Repository") and obj.__module__ == module.__name__:
                classes.add(obj)
    return classes


@pytest.mark.unit
class TestRepoBundle:
    """RepoBundle 测试。"""

    def test_all_repositories_share_one_session(self):
        """束内每个仓储的 session 必须指向同一个对象。"""
        session = MagicMock()
        bundle = RepoBundle(session)

        repos = [value for value in vars(bundle).values() if value is not session]
        assert repos, "仓储束不应为空"
        for repo in repos:
            assert repo.session is session

    def test_bundle_covers_every_repository_implementation(self):
        """infrastructure 层的每个仓储实现都要出现在束里（防漏注册）。"""
        session = MagicMock()
        bundled = {type(value) for key, value in vars(RepoBundle(session)).items() if key != "session"}

        missing = _repository_classes() - bundled
        assert not missing, f"以下仓储未纳入 RepoBundle：{sorted(cls.__name__ for cls in missing)}"


@pytest.mark.unit
class TestGetRepositories:
    """get_repositories 聚合工厂测试。"""

    async def test_returns_bundle_bound_to_request_session(self):
        """工厂应以传入的请求级 Session 建束。"""
        session = MagicMock()
        bundle = await get_repositories(db=session)

        assert isinstance(bundle, RepoBundle)
        assert bundle.session is session
        assert bundle.user.session is session
