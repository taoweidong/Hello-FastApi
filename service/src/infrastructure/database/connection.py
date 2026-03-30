"""数据库连接和会话管理。"""

from functools import partial

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True)

# 异步会话工厂，用于 CLI 脚本
async_session_factory = partial(AsyncSession, engine, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """提供异步数据库会话的依赖项。"""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """创建所有数据库表。"""
    # 导入所有模型以便它们注册到 SQLModel.metadata
    import src.infrastructure.database.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """关闭数据库引擎。"""
    await engine.dispose()
