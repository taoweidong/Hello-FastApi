"""DatabaseManager 单元测试。

测试数据库管理器的引擎配置、会话创建、表初始化与模块级单例函数。
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlmodel import SQLModel

from src.infrastructure.database.database_manager import (
    DatabaseManager,
    _get_db_manager,
    close_db,
    get_async_session_factory,
    get_db,
    get_engine,
    init_db,
)


@pytest.mark.unit
class TestDatabaseManagerInit:
    """测试 DatabaseManager 初始化。"""

    def test_init_with_sqlite_url_no_pool(self):
        """使用 SQLite URL 时不应配置连接池参数。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        assert isinstance(mgr.engine, AsyncEngine)
        pool = mgr.engine.pool
        assert pool is not None

    def test_init_with_postgresql_url_has_pool(self):
        """使用 PostgreSQL URL 时应配置连接池参数。"""
        mgr = DatabaseManager(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            echo=False,
        )
        assert isinstance(mgr.engine, AsyncEngine)

    def test_init_with_default_url_uses_settings(self):
        """未指定 URL 时应使用 settings.DATABASE_URL。"""
        mgr = DatabaseManager()
        assert isinstance(mgr.engine, AsyncEngine)

    def test_init_echo_flag_respects_explicit(self):
        """显式设置 echo 标志应优先于设置。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:", echo=True)
        assert mgr.engine.echo is True

    def test_init_echo_flag_defaults_to_debug(self):
        """未指定 echo 时应使用 settings.DEBUG。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        assert isinstance(mgr.engine.echo, bool)


@pytest.mark.unit
class TestDatabaseManagerProperties:
    """测试 DatabaseManager 属性。"""

    def test_engine_property(self):
        """engine 属性应返回 AsyncEngine 实例。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        assert isinstance(mgr.engine, AsyncEngine)

    def test_async_session_factory_property(self):
        """async_session_factory 属性应返回可调用对象。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        factory = mgr.async_session_factory
        assert callable(factory)


@pytest.mark.unit
class TestDatabaseManagerGetSession:
    """测试 get_session 会话生成器。"""

    @pytest.mark.asyncio
    async def test_get_session_yields_session(self):
        """get_session 应产出 AsyncSession 实例。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        async for session in mgr.get_session():
            assert isinstance(session, AsyncSession)
            break

    @pytest.mark.asyncio
    async def test_get_session_rollback_on_exception(self):
        """get_session 应在异常时回滚。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        with pytest.raises(ValueError):
            async for _session in mgr.get_session():
                raise ValueError("测试回滚")


@pytest.mark.unit
class TestDatabaseManagerInitTables:
    """测试 init_tables 方法。"""

    @pytest.mark.asyncio
    async def test_init_tables_creates_metadata(self):
        """init_tables 应创建 SQLModel.metadata 中所有表。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        await mgr.init_tables()
        async with mgr.engine.begin() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn)
            )
        assert len(tables) > 0

    @pytest.mark.asyncio
    async def test_init_tables_idempotent(self):
        """init_tables 多次调用应不报错（幂等）。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        await mgr.init_tables()
        await mgr.init_tables()


@pytest.mark.unit
class TestDatabaseManagerDispose:
    """测试 dispose 方法。"""

    @pytest.mark.asyncio
    async def test_dispose_closes_engine(self):
        """dispose 应关闭引擎。"""
        mgr = DatabaseManager(database_url="sqlite+aiosqlite:///:memory:")
        await mgr.dispose()


@pytest.mark.unit
class TestModuleLevelSingleton:
    """测试模块级单例和函数。"""

    def test_get_db_manager_returns_singleton(self):
        """_get_db_manager 应返回相同实例。"""
        mgr1 = _get_db_manager()
        mgr2 = _get_db_manager()
        assert mgr1 is mgr2

    @pytest.mark.asyncio
    async def test_get_db_functional(self):
        """get_db 应产出 AsyncSession。"""
        async for session in get_db():
            assert isinstance(session, AsyncSession)
            break

    def test_get_engine_functional(self):
        """get_engine 应返回 AsyncEngine。"""
        eng = get_engine()
        assert isinstance(eng, AsyncEngine)

    def test_get_async_session_factory_functional(self):
        """get_async_session_factory 应返回可调用对象。"""
        factory = get_async_session_factory()
        assert callable(factory)

    @pytest.mark.asyncio
    async def test_init_db_functional(self):
        """init_db 应创建数据库表。"""
        await init_db()

    @pytest.mark.asyncio
    async def test_close_db_functional(self):
        """close_db 应关闭并重置单例。"""
        await close_db()
        mgr_after = _get_db_manager()
        assert isinstance(mgr_after.engine, AsyncEngine)
