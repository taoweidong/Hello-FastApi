"""常见模式的装饰器。"""

import functools
from collections.abc import Callable

from src.infrastructure.logging.logger import logger


def log_execution(func: Callable) -> Callable:
    """记录函数执行时间的装饰器。"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        logger.debug(f"开始执行: {func.__name__}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"执行完成: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"执行错误 {func.__name__}: {e}")
            raise

    return wrapper
