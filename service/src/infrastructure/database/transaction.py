"""事务管理器。

提供事务装饰器和上下文管理器，确保多表操作的原子性。
"""

from collections.abc import Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import ParamSpec, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

P = ParamSpec("P")
R = TypeVar("R")


@asynccontextmanager
async def transaction(session: AsyncSession):
    """事务上下文管理器。

    Args:
        session: 数据库会话

    Yields:
        会话对象

    Raises:
        Exception: 事务中发生的任何异常，事务会自动回滚
    """
    async with session.begin():
        try:
            yield session
        except Exception:
            raise


def transactional(func: Callable[P, R]) -> Callable[P, R]:
    """事务装饰器。

    用于装饰需要在事务中执行的服务方法。

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数

    Example:
        @transactional
        async def create_user_with_role(user_dto: UserCreateDTO, role_id: str) -> UserEntity:
            user = await user_repo.create(user_entity)
            await role_repo.assign_role_to_user(user.id, role_id)
            return user
    """

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        session = kwargs.get("session")
        if session is None:
            raise ValueError("session parameter is required for transactional methods")

        async with session.begin():
            return await func(*args, **kwargs)

    return wrapper
