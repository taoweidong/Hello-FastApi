"""审计日志批量落库队列的单元测试。

验证：
- 队列未启动时 running=False（中间件据此走历史兜底直写路径）；
- 攒批落库 executemany 语义（单会话单次往返）+ count 缓存失效；
- worker 停止时 flush 余量；
- 队列满时丢弃并返回 False（不阻塞响应）。

worker 主循环的批采集依赖真实事件循环计时，通过轮询 flush 调用断言，
避免 sleep 固定时长的脆弱断言。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.http.audit_log_queue import AuditLogQueue, get_audit_log_queue


def _row(seq: int) -> dict:
    """构造一条最小审计日志行。"""
    return {"id": f"log-{seq}", "module": "user", "method": "POST", "path": "/api/system/user"}


async def _wait_for(predicate, timeout: float = 3.0, interval: float = 0.05) -> bool:
    """轮询等待条件成立（避免固定 sleep 的脆弱断言）。"""
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if predicate():
            return True
        await asyncio.sleep(interval)
    return predicate()


@pytest.mark.unit
class TestAuditLogQueueLifecycle:
    """队列生命周期语义。"""

    @pytest.mark.asyncio
    async def test_not_running_before_start(self):
        """未启动时 running=False（测试环境 empty_lifespan 即此状态）。"""
        queue = AuditLogQueue()
        assert queue.running is False

    @pytest.mark.asyncio
    async def test_start_makes_running_and_stop_clears(self):
        """start 后 running=True，stop 后回到 False。"""
        queue = AuditLogQueue()
        queue.start()
        assert queue.running is True
        await queue.stop()
        assert queue.running is False

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self):
        """重复 start 不产生新 worker 任务。"""
        queue = AuditLogQueue()
        queue.start()
        first_worker = queue._worker
        queue.start()
        assert queue._worker is first_worker
        await queue.stop()

    @pytest.mark.asyncio
    async def test_stop_without_start_is_noop(self):
        """未启动时 stop 直接返回，不抛异常。"""
        queue = AuditLogQueue()
        await queue.stop()
        assert queue._worker is None

    @pytest.mark.asyncio
    async def test_module_singleton_is_stable(self):
        """模块级单例：多次获取返回同一实例。"""
        assert get_audit_log_queue() is get_audit_log_queue()


@pytest.mark.unit
class TestAuditLogQueueEnqueue:
    """入队语义。"""

    @pytest.mark.asyncio
    async def test_enqueue_returns_true_and_queues(self):
        """未满时入队成功。"""
        queue = AuditLogQueue()
        assert queue.enqueue(_row(1)) is True
        assert queue._queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_enqueue_full_queue_drops_without_blocking(self):
        """队列满时丢弃该条并返回 False（审计尽力而为，不阻塞响应）。"""
        queue = AuditLogQueue()
        small = asyncio.Queue(maxsize=1)
        small.put_nowait(_row(1))
        queue._queue = small
        assert queue.enqueue(_row(2)) is False


@pytest.mark.unit
class TestAuditLogQueueFlush:
    """批量落库语义。"""

    def _fake_session_factory(self):
        """构造带 AsyncMock 会话的会话工厂替身。"""
        mock_session = MagicMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        factory = MagicMock(return_value=mock_session)
        return factory, mock_session

    @pytest.mark.asyncio
    async def test_flush_executes_single_insert_and_commits(self):
        """一批日志单会话单次 executemany 落库并提交。"""
        queue = AuditLogQueue()
        factory, mock_session = self._fake_session_factory()
        with (
            patch.object(AuditLogQueue, "_get_session_factory", return_value=factory),
            patch.object(AuditLogQueue, "_invalidate_log_count_cache", new_callable=AsyncMock) as mock_invalidate,
        ):
            await queue._flush([_row(1), _row(2), _row(3)])

        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()
        mock_invalidate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_flush_empty_rows_is_noop(self):
        """空批次直接返回，不触碰数据库。"""
        queue = AuditLogQueue()
        factory, mock_session = self._fake_session_factory()
        with patch.object(AuditLogQueue, "_get_session_factory", return_value=factory):
            await queue._flush([])
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_flush_error_does_not_raise(self):
        """落库失败仅告警，不向 worker 循环抛异常。"""
        queue = AuditLogQueue()
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(side_effect=Exception("数据库不可用"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        factory = MagicMock(return_value=mock_session)
        with patch.object(AuditLogQueue, "_get_session_factory", return_value=factory):
            # 不抛异常即通过
            await queue._flush([_row(1)])

    @pytest.mark.asyncio
    async def test_flush_invalidates_count_cache_with_db_failure_skipped(self):
        """落库失败时不失效 count 缓存（缓存内容仍与库一致）。"""
        queue = AuditLogQueue()
        mock_session = MagicMock()
        mock_session.execute = AsyncMock(side_effect=Exception("数据库不可用"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        factory = MagicMock(return_value=mock_session)
        with (
            patch.object(AuditLogQueue, "_get_session_factory", return_value=factory),
            patch.object(AuditLogQueue, "_invalidate_log_count_cache", new_callable=AsyncMock) as mock_invalidate,
        ):
            await queue._flush([_row(1)])
        mock_invalidate.assert_not_awaited()


@pytest.mark.unit
class TestAuditLogQueueWorker:
    """worker 攒批与停止 flush 余量语义。"""

    @pytest.mark.asyncio
    async def test_worker_flushes_enqueued_rows_and_stop_drains_remainder(self):
        """worker 消费入队日志；停止时排空余量，最终全部落库、无丢失。"""
        queue = AuditLogQueue()
        flushed: list[list[dict]] = []

        async def fake_flush(rows: list[dict]) -> None:
            flushed.append(rows)

        with patch.object(queue, "_flush", side_effect=fake_flush):
            queue.start()
            for i in range(10):
                queue.enqueue(_row(i))
            # 等待队列被消费（worker 首条等待至多 1s）
            drained = await _wait_for(lambda: queue._queue.qsize() == 0 and len(flushed) >= 1)
            assert drained, "worker 未在超时内消费队列"
            await queue.stop()
            # 停止后余量 flush 完成：总条数不丢
            assert queue._queue.qsize() == 0
        assert sum(len(batch) for batch in flushed) == 10

    @pytest.mark.asyncio
    async def test_worker_batches_within_max_size(self):
        """单批不超过 BATCH_SIZE 上限（50 条）。"""
        from src.infrastructure.http.audit_log_queue import BATCH_SIZE

        queue = AuditLogQueue()
        flushed: list[list[dict]] = []

        async def fake_flush(rows: list[dict]) -> None:
            flushed.append(rows)

        with patch.object(queue, "_flush", side_effect=fake_flush):
            queue.start()
            for i in range(BATCH_SIZE + 30):
                queue.enqueue(_row(i))
            await _wait_for(lambda: sum(len(b) for b in flushed) >= BATCH_SIZE + 30)
            await queue.stop()

        assert sum(len(batch) for batch in flushed) == BATCH_SIZE + 30
        assert all(len(batch) <= BATCH_SIZE for batch in flushed)
