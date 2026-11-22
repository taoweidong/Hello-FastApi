"""应用层 - 日志服务。

提供日志相关的业务逻辑，包括登录日志和操作日志的查询和管理。
操作/系统日志列表支持 keyset 深分页游标与 total 缓存（logs:count:{filters_hash}）：
首页执行精确 COUNT 并回填缓存，深页（游标/offset>0）优先复用缓存 total，
消除深分页每页一次的精确 COUNT 开销。
"""

import hashlib
import json
from datetime import datetime

from src.domain.repositories.log_repository import LogRepositoryInterface
from src.domain.services.cache_port import LogCountCachePort


def _parse_log_time_bound(value: object) -> datetime | None:
    """解析日志时间边界值。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


def _hash_log_filters(
    module: str | None, status_code: int | None, start_time: datetime | None, end_time: datetime | None
) -> str:
    """对筛选条件做稳定序列化后哈希（count 缓存 Key 的后缀）。

    只覆盖影响结果集的过滤字段，不含分页/游标（同一筛选下各页共享同一 total）。
    """
    raw = json.dumps(
        {
            "module": module or "",
            "status_code": status_code if status_code is not None else "",
            "start": start_time.isoformat() if start_time else "",
            "end": end_time.isoformat() if end_time else "",
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


class LogService:
    """日志领域操作的应用服务。"""

    def __init__(self, log_repo: LogRepositoryInterface, count_cache: LogCountCachePort | None = None):
        self.log_repo = log_repo
        self.count_cache = count_cache

    # ============ 登录日志 ============

    async def get_login_logs(self, query) -> tuple[list, int]:
        """获取登录日志列表。"""
        start_time = None
        end_time = None
        if query.createdTime and isinstance(query.createdTime, list) and len(query.createdTime) == 2:
            start_time = _parse_log_time_bound(query.createdTime[0])
            end_time = _parse_log_time_bound(query.createdTime[1])

        status = None
        if query.status:
            status = int(query.status)

        logs, total = await self.log_repo.get_login_logs(
            page_num=query.pageNum, page_size=query.pageSize, status=status, start_time=start_time, end_time=end_time
        )
        return logs, total

    async def delete_login_logs(self, dto) -> int:
        """批量删除登录日志。"""
        count = await self.log_repo.delete_login_logs(log_ids=dto.ids)
        return count

    async def clear_login_logs(self) -> int:
        """清空所有登录日志。"""
        return await self.log_repo.clear_login_logs()

    # ============ 操作日志（统一日志表 sys_logs） ============

    async def get_operation_logs(self, query) -> tuple[list, int]:
        """获取操作日志列表（keyset 深分页 + total 缓存）。"""
        return await self._get_sys_logs(query, self.log_repo.get_operation_logs)

    async def delete_operation_logs(self, dto) -> int:
        """批量删除操作日志。"""
        count = await self.log_repo.delete_operation_logs(log_ids=dto.ids)
        return count

    async def clear_operation_logs(self) -> int:
        """清空所有操作日志。"""
        return await self.log_repo.clear_operation_logs()

    # ============ 系统日志（与操作日志共享 sys_logs 表） ============

    async def get_system_logs(self, query) -> tuple[list, int]:
        """获取系统日志列表（keyset 深分页 + total 缓存）。"""
        return await self._get_sys_logs(query, self.log_repo.get_system_logs)

    async def get_system_log_detail(self, log_id: str):
        """获取系统日志详情。"""
        return await self.log_repo.get_system_log_detail(log_id=log_id)

    # ============ 操作/系统日志共享的列表与 COUNT 策略 ============

    async def _get_sys_logs(self, query, repo_fn) -> tuple[list, int]:
        """操作/系统日志共享的列表查询（COUNT 策略：首页精确值回填缓存，深页复用缓存）。

        repo_fn：仓储列表方法（操作/系统日志共享同一张表与同一实现签名）。

        - 首页（无游标且 pageNum<=1）：仓储执行精确 COUNT，结果写入
          ``logs:count:{filters_hash}``（TTL 60s，由审计落库 worker 或 TTL 失效）；
        - 深页（游标或 pageNum>1）：优先读缓存 total 跳过 COUNT；
          缓存未命中时兜底执行 COUNT 并回填，保证 total 语义正确。
        """
        start_time, end_time, status_code, before_time, before_id = self._parse_sys_query(query)

        cursor_mode = before_time is not None and bool(before_id)
        filters_hash = _hash_log_filters(query.module, status_code, start_time, end_time)
        # 首页 = 无游标且第一页（offset=0）：始终精确 COUNT
        first_page = not cursor_mode and (query.pageNum or 1) <= 1

        total: int | None = None
        if not first_page and self.count_cache is not None:
            total = await self.count_cache.get_log_count(filters_hash)

        logs, total = await repo_fn(
            page_num=query.pageNum,
            page_size=query.pageSize,
            module=query.module,
            status_code=status_code,
            start_time=start_time,
            end_time=end_time,
            before_time=before_time if cursor_mode else None,
            before_id=before_id if cursor_mode else None,
            total=total,
        )

        # 回填缓存：首页精确值 / 深页兜底计算值（缓存写入失败不影响响应）
        if self.count_cache is not None:
            await self.count_cache.set_log_count(filters_hash, total)
        return logs, total

    @staticmethod
    def _parse_sys_query(query) -> tuple[datetime | None, datetime | None, int | None, datetime | None, str | None]:
        """解析操作/系统日志列表查询的时间范围、状态码与 keyset 游标。"""
        start_time = None
        end_time = None
        if query.createdTime and isinstance(query.createdTime, list) and len(query.createdTime) == 2:
            start_time = _parse_log_time_bound(query.createdTime[0])
            end_time = _parse_log_time_bound(query.createdTime[1])

        status_code = None
        if query.status:
            status_code = int(query.status)

        before_time = _parse_log_time_bound(getattr(query, "beforeTime", None))
        before_id = (getattr(query, "beforeId", None) or "").strip() or None
        return start_time, end_time, status_code, before_time, before_id
