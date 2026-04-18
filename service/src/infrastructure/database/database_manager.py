"""数据库连接和会话管理器。"""

from collections.abc import AsyncGenerator
from functools import partial

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.settings import settings


class DatabaseManager:
    """数据库管理器，封装引擎、会话工厂和生命周期。"""

    def __init__(self, database_url: str | None = None, echo: bool | None = None) -> None:
        url = database_url or settings.DATABASE_URL
        echo_flag = echo if echo is not None else settings.DEBUG
        self._engine = create_async_engine(url, echo=echo_flag, pool_pre_ping=True)

        # 为 SQLite 启用外键约束
        if url.startswith("sqlite"):
            @event.listens_for(self._engine.sync_engine, "connect")
            def _set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self._async_session_factory = partial(AsyncSession, self._engine, expire_on_commit=False)

    @property
    def engine(self):
        """获取数据库引擎。"""
        return self._engine

    @property
    def async_session_factory(self):
        """获取异步会话工厂（用于 CLI 脚本）。"""
        return self._async_session_factory

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """提供异步数据库会话的生成器。"""
        async with AsyncSession(self._engine, expire_on_commit=False) as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def init_tables(self) -> None:
        """创建所有数据库表。"""
        import src.infrastructure.database.models  # noqa: F401

        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    async def dispose(self) -> None:
        """关闭数据库引擎。"""
        await self._engine.dispose()


# ── 模块级单例 & 兼容函数 ──────────────────────────────────────────

_db_manager: DatabaseManager | None = None


def _get_db_manager() -> DatabaseManager:
    """获取或创建 DatabaseManager 单例。"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """提供异步数据库会话的依赖项（兼容 FastAPI Depends）。"""
    manager = _get_db_manager()
    async for session in manager.get_session():
        yield session


async def init_db() -> None:
    """创建所有数据库表。"""
    manager = _get_db_manager()
    await manager.init_tables()


async def close_db() -> None:
    """关闭数据库引擎。"""
    global _db_manager
    if _db_manager is not None:
        await _db_manager.dispose()
        _db_manager = None


def get_engine():
    """获取数据库引擎。"""
    return _get_db_manager().engine


def get_async_session_factory():
    """获取异步会话工厂。"""
    return _get_db_manager().async_session_factory
