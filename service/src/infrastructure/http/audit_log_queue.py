"""审计日志批量落库队列。

进程内 ``asyncio.Queue`` + 单后台 worker：把请求日志中间件产生的审计日志
攒批（≤``BATCH_SIZE`` 条或 ≤``FLUSH_INTERVAL`` 秒）后以 executemany 形式
一次落库，消除"每请求独立会话 + 逐条 INSERT"的写放大与连接开销。

生命周期约定：
- 生产/开发环境由 ``application_lifespan`` 启动（``start``）与停止（``stop``）；
  停止时先排空队列余量再退出 worker，保证最后一批审计不丢。
- 测试环境（``empty_lifespan``）worker 不启动；此时中间件检测到
  ``running`` 为 False，退化为历史的"后台任务独立会话直写"路径，
  保证现有集成测试对"请求返回后日志立即可查"的断言零改动通过。
"""

import asyncio
from typing import Any

from sqlalchemy import insert as sa_insert

from src.infrastructure.logging.logger import logger

# 攒批上限：单批最多落库条数
BATCH_SIZE = 50
# 攒批时限：首条入队后最多等待的秒数（低流量下避免审计延迟超过 1s）
FLUSH_INTERVAL = 1.0
# 队列容量上限：突发流量下超过容量的审计日志直接丢弃（审计尽力而为，不阻塞响应）
QUEUE_MAX_SIZE = 10000
# 日志列表 count 缓存（logs:count:*）的前缀：批量落库后统一失效
_LOG_COUNT_CACHE_PREFIX = "logs:count:"


class AuditLogQueue:
    """审计日志批量落库队列（进程内单例）。"""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
        self._worker: asyncio.Task[None] | None = None
        self._stopping = False

    @property
    def running(self) -> bool:
        """worker 是否已启动且未进入停止流程。"""
        return self._worker is not None and not self._stopping

    def start(self) -> None:
        """启动后台 worker（幂等：重复调用不产生新任务）。"""
        if self._worker is not None and not self._worker.done():
            return
        self._stopping = False
        self._worker = asyncio.create_task(self._run(), name="audit-log-queue-worker")

    async def stop(self, timeout: float = 5.0) -> None:
        """停止 worker 并 flush 队列余量（幂等：未启动时直接返回）。

        Args:
            timeout: 等待余量落库的超时秒数，超时后取消 worker（避免阻塞关闭流程）。
        """
        if self._worker is None:
            return
        self._stopping = True
        worker = self._worker
        self._worker = None
        try:
            # worker 感知 _stopping 后会先排空队列余量再退出
            await asyncio.wait_for(asyncio.shield(worker), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("审计日志 worker 停止超时，取消任务并放弃余量")
            worker.cancel()
        except asyncio.CancelledError:
            pass

    def enqueue(self, row: dict[str, Any]) -> bool:
        """将一条审计日志入队（非阻塞）。

        Returns:
            是否成功入队；队列已满时丢弃该条并告警（审计尽力而为，不阻塞响应）。
        """
        try:
            self._queue.put_nowait(row)
            return True
        except asyncio.QueueFull:
            logger.warning("审计日志队列已满，丢弃本条审计日志（不阻塞响应）")
            return False

    async def _run(self) -> None:
        """worker 主循环：攒批（≤BATCH_SIZE 条或 ≤FLUSH_INTERVAL 秒）后落库。"""
        loop = asyncio.get_running_loop()
        while not self._stopping:
            rows: list[dict[str, Any]] = []
            try:
                # 等首条（带超时以便感知停止信号）
                first = await asyncio.wait_for(self._queue.get(), timeout=FLUSH_INTERVAL)
            except (asyncio.TimeoutError, TimeoutError):
                continue
            rows.append(first)
            # 截止时间内继续收批
            deadline = loop.time() + FLUSH_INTERVAL
            while len(rows) < BATCH_SIZE:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    break
                try:
                    rows.append(await asyncio.wait_for(self._queue.get(), timeout=remaining))
                except (asyncio.TimeoutError, TimeoutError):
                    break
            await self._flush(rows)
        # 停止流程：排空队列余量后退出（保证最后一批审计不丢）
        await self._drain_remaining()

    @staticmethod
    def _get_session_factory():
        """获取异步会话工厂（独立小方法便于测试替身注入）。"""
        from src.infrastructure.database import get_async_session_factory

        return get_async_session_factory()

    async def _flush(self, rows: list[dict[str, Any]]) -> None:
        """批量落库一批审计日志（executemany 形式，单会话单次往返）。"""
        if not rows:
            return
        try:
            from src.infrastructure.database.models import SystemLog

            session_factory = self._get_session_factory()
            async with session_factory() as session:
                await session.execute(sa_insert(SystemLog), rows)
                await session.commit()
        except Exception:
            logger.warning(f"审计日志批量落库失败，丢失 {len(rows)} 条", exc_info=True)
            return
        # 落库成功后统一失效日志列表 count 缓存（logs:count:*）：
        # 新增审计会使列表 total 变化，60s TTL 是兜底，worker 侧失效保证近实时
        await self._invalidate_log_count_cache()

    @staticmethod
    async def _invalidate_log_count_cache() -> None:
        """按前缀失效日志列表 count 缓存（Redis 未配置/不可用时静默跳过，TTL 兜底）。"""
        try:
            from src.infrastructure.cache.redis_manager import get_redis

            redis_client = await get_redis()
            keys = [key async for key in redis_client.scan_iter(match=f"{_LOG_COUNT_CACHE_PREFIX}*", count=100)]
            if keys:
                await redis_client.delete(*keys)
        except Exception:
            logger.debug("失效日志 count 缓存跳过（Redis 未配置或不可用，依赖 TTL 兜底）")

    async def _drain_remaining(self) -> None:
        """排空队列余量并落库（停止流程调用）。"""
        rows: list[dict[str, Any]] = []
        while True:
            try:
                rows.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        await self._flush(rows)


# 模块级单例
_audit_log_queue: AuditLogQueue | None = None


def get_audit_log_queue() -> AuditLogQueue:
    """获取审计日志队列单例。"""
    global _audit_log_queue
    if _audit_log_queue is None:
        _audit_log_queue = AuditLogQueue()
    return _audit_log_queue
