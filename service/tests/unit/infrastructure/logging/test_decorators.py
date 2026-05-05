"""log_execution 装饰器单元测试。

测试装饰器在异步函数正常执行和异常抛出时的日志记录行为。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.logging.decorators import log_execution


@pytest.mark.unit
class TestLogExecution:
    """log_execution 装饰器测试。"""

    @pytest.mark.asyncio
    async def test_decorator_logs_start_and_end(self):
        """测试装饰器记录开始和完成日志。"""
        mock_logger = MagicMock()

        @log_execution
        async def sample_func(x: int) -> int:
            return x * 2

        with patch("src.infrastructure.logging.decorators.logger", mock_logger):
            result = await sample_func(5)

        assert result == 10
        mock_logger.debug.assert_any_call("开始执行: sample_func")
        mock_logger.debug.assert_any_call("执行完成: sample_func")

    @pytest.mark.asyncio
    async def test_decorator_logs_and_reraises_error(self):
        """测试装饰器在函数异常时记录错误并重新抛出。"""
        mock_logger = MagicMock()

        @log_execution
        async def failing_func() -> None:
            msg = "出错了"
            raise ValueError(msg)

        with patch("src.infrastructure.logging.decorators.logger", mock_logger):
            with pytest.raises(ValueError, match="出错了"):
                await failing_func()

        mock_logger.debug.assert_any_call("开始执行: failing_func")
        mock_logger.error.assert_called_once()
        assert "failing_func" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_preserves_function_name(self):
        """测试装饰器保留原函数名称。"""

        @log_execution
        async def my_test_func() -> None:
            pass

        assert my_test_func.__name__ == "my_test_func"

    @pytest.mark.asyncio
    async def test_preserves_docstring(self):
        """测试装饰器保留原函数文档字符串。"""

        @log_execution
        async def documented_func() -> None:
            """这是一个测试函数。"""

        assert documented_func.__doc__ == "这是一个测试函数。"

    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs(self):
        """测试装饰器正确传递位置和关键字参数。"""
        mock_logger = MagicMock()
        mock_target = AsyncMock(return_value="done")

        @log_execution
        async def target_func(*args: object, **kwargs: object) -> str:
            return await mock_target(*args, **kwargs)

        with patch("src.infrastructure.logging.decorators.logger", mock_logger):
            result = await target_func(1, 2, key="val")

        assert result == "done"
        mock_target.assert_called_once_with(1, 2, key="val")

    @pytest.mark.asyncio
    async def test_decorator_async_function_detection(self):
        """测试装饰器可以装饰真正的异步函数。"""

        @log_execution
        async def async_func() -> str:
            return "async result"

        coro = async_func()
        result = await coro
        assert result == "async result"

    @pytest.mark.asyncio
    async def test_decorator_empty_function(self):
        """测试装饰器装饰无返回值的异步函数。"""

        @log_execution
        async def empty_func() -> None:
            pass

        mock_logger = MagicMock()
        with patch("src.infrastructure.logging.decorators.logger", mock_logger):
            await empty_func()

        mock_logger.debug.assert_any_call("开始执行: empty_func")
        mock_logger.debug.assert_any_call("执行完成: empty_func")

    @pytest.mark.asyncio
    async def test_decorator_with_kwargs_only(self):
        """测试装饰器仅传关键字参数。"""

        @log_execution
        async def kwarg_func(**kwargs: object) -> dict:
            return kwargs

        mock_logger = MagicMock()
        with patch("src.infrastructure.logging.decorators.logger", mock_logger):
            result = await kwarg_func(a=1, b=2)

        assert result == {"a": 1, "b": 2}
