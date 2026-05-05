"""Alembic 环境配置，适配 SQLModel + async engine。"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# 注册所有模型（确保 metadata 包含所有表）
import src.infrastructure.database.models  # noqa: F401
from src.config.settings import Settings

config = context.config

# 从 .env 文件读取 DATABASE_URL 覆盖 alembic.ini 中的占位符
_settings = Settings()
if config.config_file_name is not None:
    config.set_main_option("sqlalchemy.url", _settings.DATABASE_URL)

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本而不连接数据库。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """在线模式：实际连接数据库执行迁移。"""
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步迁移入口。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口。"""
    url = config.get_main_option("sqlalchemy.url")
    if url and url.startswith("sqlite"):
        # SQLite 不支持 async driver 的某些操作，使用 sync 模式
        from sqlalchemy import create_engine

        sync_url = url.replace("sqlite+aiosqlite://", "sqlite://")
        connectable = create_engine(sync_url, poolclass=pool.NullPool)
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
