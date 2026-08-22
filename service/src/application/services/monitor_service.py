"""应用层 - 系统监控服务。

采集服务器资源（CPU/内存/磁盘/系统/进程）与 Redis 缓存运行状态，
供监控页面展示。对标 RuoYi 服务器监控与缓存监控。
"""

import os
import platform
import time
from datetime import datetime, timedelta, timezone

import psutil
from loguru import logger

from src.application.dto.monitor_dto import (
    CacheCommandStatDTO,
    CacheInfoDTO,
    CpuInfoDTO,
    DiskInfoDTO,
    MemoryInfoDTO,
    OnlineLogsQueryDTO,
    ProcessInfoDTO,
    ServerInfoDTO,
    SystemInfoDTO,
)
from src.config.settings import settings
from src.domain.services.cache_port import CachePort

_GB = 1024**3


def _format_gb(num_bytes: int | float) -> str:
    """将字节数格式化为 GB 字符串（保留两位小数）。"""
    return f"{num_bytes / _GB:.2f} GB"


def _format_duration(seconds: float) -> str:
    """将秒数格式化为 `X天X小时X分钟X秒` 形式。"""
    seconds = max(int(seconds), 0)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}天")
    if hours:
        parts.append(f"{hours}小时")
    if minutes:
        parts.append(f"{minutes}分钟")
    parts.append(f"{secs}秒")
    return "".join(parts)


class MonitorService:
    """系统监控服务：无状态采集器，不依赖数据库。"""

    def __init__(self, cache_service: CachePort | None = None) -> None:
        """初始化监控服务。

        Args:
            cache_service: 缓存服务端口（用于在线用户会话查询与强制下线），可为 None 触发降级
        """
        self.cache_service = cache_service

    async def get_online_logs(self, query: OnlineLogsQueryDTO) -> tuple[list[dict], int]:
        """获取在线用户会话列表（支持用户名过滤与分页）。

        Args:
            query: 查询参数（username/page_num/page_size）

        Returns:
            (当前页会话列表, 总条数)；缓存未注入或不可用时降级返回空列表
        """
        if self.cache_service is None:
            return [], 0
        sessions = await self.cache_service.get_online_users()
        if query.username:
            keyword = query.username.strip().lower()
            sessions = [item for item in sessions if keyword in str(item.get("username") or "").lower()]
        # 按登录时间倒序排列
        sessions.sort(key=lambda item: str(item.get("loginTime") or ""), reverse=True)
        total = len(sessions)
        start = (query.page_num - 1) * query.page_size
        page_items = sessions[start : start + query.page_size]
        return page_items, total

    async def force_offline(self, session_key: str) -> bool:
        """强制下线指定在线会话。

        删除 Redis 在线会话，并将该会话 Token 哈希加入黑名单，
        使其下一次调用被认证中间件拦截。会话不存在时同样返回成功（幂等）。

        Args:
            session_key: 在线会话 Key（访问令牌哈希前缀）

        Returns:
            是否执行成功；缓存未注入时返回 False
        """
        if self.cache_service is None:
            return False
        # 先读取会话的过期时间（用作黑名单 TTL），再删除会话
        session = await self.cache_service.get_online_user(session_key)
        await self.cache_service.delete_online_user(session_key)
        expires_at: datetime | None = None
        if session and session.get("expiresAt"):
            try:
                expires_at = datetime.fromisoformat(str(session["expiresAt"]))
            except (TypeError, ValueError):
                expires_at = None
        if expires_at is None:
            # 会话信息缺失或已过期：兜底使用默认黑名单保留时长
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.CACHE_TOKEN_BLACKLIST_TTL)
        await self.cache_service.blacklist_token_hash(session_key, expires_at)
        return True

    async def get_server_info(self) -> ServerInfoDTO:
        """采集服务器资源信息（CPU/内存/磁盘/系统/进程）。"""
        # CPU：采样间隔取较小值，兼顾准确性与接口响应速度
        cpu_percent = psutil.cpu_percent(interval=0.1)
        core_count = psutil.cpu_count(logical=True) or 1

        # 内存
        vmem = psutil.virtual_memory()

        # 磁盘：以当前工作目录所在分区为准，兼容 Windows 与 Unix
        disk = psutil.disk_usage(os.getcwd())

        # 系统信息
        system_info = SystemInfoDTO(
            hostname=platform.node(),
            osName=platform.platform(),
            osArch=platform.machine(),
            pythonVersion=platform.python_version(),
            workDir=os.getcwd(),
            bootTime=datetime.fromtimestamp(psutil.boot_time()),
        )

        # 当前服务进程信息
        process = psutil.Process(os.getpid())
        process_info = ProcessInfoDTO(
            pid=os.getpid(),
            memoryUsed=_format_gb(process.memory_info().rss),
            cpuPercent=process.cpu_percent(interval=0.1),
            runningTime=_format_duration(time.time() - process.create_time()),
        )

        return ServerInfoDTO(
            cpu=CpuInfoDTO(coreCount=core_count, usedPercent=cpu_percent),
            memory=MemoryInfoDTO(
                total=_format_gb(vmem.total),
                used=_format_gb(vmem.used),
                free=_format_gb(vmem.available),
                usedPercent=vmem.percent,
            ),
            disk=DiskInfoDTO(
                total=_format_gb(disk.total),
                used=_format_gb(disk.used),
                free=_format_gb(disk.free),
                usedPercent=disk.percent,
            ),
            system=system_info,
            process=process_info,
        )

    async def get_cache_info(self, redis_client: object | None) -> CacheInfoDTO:
        """采集 Redis 缓存运行状态。

        redis_client 为 None 或命令执行失败时返回降级响应（connected=False），不抛异常。
        """
        if redis_client is None:
            return CacheInfoDTO(connected=False, message="Redis 服务不可用或未配置")
        try:
            info: dict = await redis_client.info()  # type: ignore[attr-defined]
            key_count: int = await redis_client.dbsize()  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 —— 监控接口不允许因 Redis 故障而报错
            logger.warning(f"缓存监控采集失败，返回降级响应：{exc}")
            return CacheInfoDTO(connected=False, message=f"Redis 连接失败：{exc}")

        # 命中率：keyspace_hits / (hits + misses)
        hits = int(info.get("keyspace_hits") or 0)
        misses = int(info.get("keyspace_misses") or 0)
        hit_rate = round(hits / (hits + misses) * 100, 2) if (hits + misses) > 0 else None

        # 命令统计：Redis 5.0 默认 INFO 输出不含 cmdstat_* 段，需显式查询 commandstats
        try:
            cmd_info: dict = await redis_client.info("commandstats")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 —— 老版本客户端或无该段时退化为默认 INFO
            cmd_info = info
        command_stats: list[CacheCommandStatDTO] = []
        for key, value in cmd_info.items():
            if not isinstance(key, str) or not key.startswith("cmdstat_"):
                continue
            stat = value if isinstance(value, dict) else {}
            command_stats.append(
                CacheCommandStatDTO(
                    name=key.removeprefix("cmdstat_"),
                    calls=int(stat.get("calls") or 0),
                    usec=int(stat.get("usec") or 0),
                )
            )
        command_stats.sort(key=lambda item: item.calls, reverse=True)

        return CacheInfoDTO(
            connected=True,
            version=str(info.get("redis_version") or "") or None,
            mode=str(info.get("redis_mode") or "") or None,
            uptimeSeconds=int(info.get("uptime_in_seconds") or 0) or None,
            usedMemory=str(info.get("used_memory_human") or "") or None,
            usedMemoryPeak=str(info.get("used_memory_peak_human") or "") or None,
            keyCount=int(key_count),
            hitRate=hit_rate,
            clients=int(info.get("connected_clients") or 0) or None,
            commandStats=command_stats[:10],
        )
