"""常见模式的装饰器。"""

import functools
from collections.abc import Callable

from src.core.logger import logger


def log_execution(func: Callable) -> Callable:
    """记录函数执行时间的装饰器。"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        logger.debug(f"Executing {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise

    return wrapper
