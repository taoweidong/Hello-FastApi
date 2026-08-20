"""应用层 - 系统监控服务。

采集服务器资源（CPU/内存/磁盘/系统/进程）与 Redis 缓存运行状态，
供监控页面展示。对标 RuoYi 服务器监控与缓存监控。
"""

import os
import platform
import time
from datetime import datetime

import psutil
from loguru import logger

from src.application.dto.monitor_dto import (
    CacheCommandStatDTO,
    CacheInfoDTO,
    CpuInfoDTO,
    DiskInfoDTO,
    MemoryInfoDTO,
    ProcessInfoDTO,
    ServerInfoDTO,
    SystemInfoDTO,
)

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

        # 命令统计：解析 info 中的 cmdstat_* 段，按调用次数取 Top10
        command_stats: list[CacheCommandStatDTO] = []
        for key, value in info.items():
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
