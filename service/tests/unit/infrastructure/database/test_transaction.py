"""transaction 模块单元测试。

测试 transaction 上下文管理器和 transactional 装饰器的所有代码路径与分支。
"""

from unittest.mock import Mock

import pytest

from src.infrastructure.database.transaction import transaction, transactional


class MockAsyncCM:
    """手动实现异步上下文管理器，避免 AsyncMock 子 mock 协议问题。"""

    def __init__(self):
        self.entered = False
        self.exited = False
        self.exit_exc_type = None
        self.exit_exc_val = None
        self.exit_tb = None

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        self.exited = True
        self.exit_exc_type = exc_type
        self.exit_exc_val = exc_val
        self.exit_tb = tb
        return False


def make_mock_session():
    """构建一个支持 ``async with session.begin()`` 的 Mock 对象。"""
    cm = MockAsyncCM()
    session = Mock()
    session.begin = Mock(return_value=cm)
    return session, cm


@pytest.mark.unit
class TestTransactionContextManager:
    """测试 transaction 异步上下文管理器。"""

    @pytest.mark.asyncio
    async def test_transaction_happy_path_commits(self):
        """无异常时 session.begin() 正常进入并退出，事务提交。"""
        session, cm = make_mock_session()

        async with transaction(session) as sess:
            assert sess is session

        assert session.begin.call_count == 1
        assert cm.entered is True
        assert cm.exited is True
        assert cm.exit_exc_type is None

    @pytest.mark.asyncio
    async def test_transaction_exception_propagates(self):
        """上下文内抛出异常时应向上传播，session.begin() 的 __aexit__ 接收 exc_info。"""
        session, cm = make_mock_session()

        with pytest.raises(ValueError, match="test error"):
            async with transaction(session) as sess:
                assert sess is session
                raise ValueError("test error")

        assert session.begin.call_count == 1
        assert cm.entered is True
        assert cm.exited is True
        assert cm.exit_exc_type is ValueError


@pytest.mark.unit
class TestTransactionalDecorator:
    """测试 transactional 装饰器。"""

    @pytest.mark.asyncio
    async def test_transactional_missing_session_key_raises(self):
        """kwargs 中不存在 session 键时应抛出 ValueError。"""

        @transactional
        async def sample_func(x: int) -> int:
            return x * 2

        with pytest.raises(
            ValueError, match="session parameter is required for transactional methods"
        ):
            await sample_func(x=10)

    @pytest.mark.asyncio
    async def test_transactional_session_none_raises(self):
        """session=None 显式传入时应抛出 ValueError。"""

        @transactional
        async def sample_func(x: int) -> int:
            return x * 2

        with pytest.raises(
            ValueError, match="session parameter is required for transactional methods"
        ):
            await sample_func(x=10, session=None)

    @pytest.mark.asyncio
    async def test_transactional_happy_path(self):
        """传入有效 session 时正常包装调用，函数执行一次并返回结果。"""
        session, cm = make_mock_session()

        @transactional
        async def sample_func(x: int, y: int, **kwargs) -> int:
            return x + y

        result = await sample_func(x=3, y=7, session=session)

        assert result == 10
        assert session.begin.call_count == 1
        assert cm.entered is True
        assert cm.exited is True
