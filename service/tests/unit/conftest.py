"""tests/unit 级 conftest：覆盖根级 conftest 的 DB 自动建表。

根级 conftest 的 setup_database（autouse）对每个测试执行 create_all + drop_all，
对不碰数据库的纯逻辑单测是纯开销（约 2091 用例 × 2 次 DDL ≈ 全程一半耗时）。
unit 层测试要么使用内存替身（fakes/AsyncMock），要么自带局部 fixture 构建
TestClient 并覆盖依赖，均不需要真实数据库。

需要真实 DB 的契约测试放在 tests/integration/（根级 autouse 在该目录仍然生效）。
"""

import pytest


@pytest.fixture(autouse=True)
def setup_database():
    """unit 层空实现：遮蔽根级 conftest 的建表/删表 autouse fixture。"""
    yield


@pytest.fixture(autouse=True)
async def _dispose_leaked_engines():
    """兜底：释放测试期间泄漏的数据库管理器单例。

    部分单测会触发真实引擎（如后台审计写库），连接对应的 aiosqlite
    工作线程是非守护线程——不 dispose 会让 pytest 在测试全部通过后
    卡在进程退出阶段（曾浪费每轮全量 5 分钟以上）。
    """
    yield
    from src.infrastructure.database.database_manager import close_db

    await close_db()
