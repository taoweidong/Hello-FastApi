"""应用层 - 系统监控领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_to_none


class OnlineLogsQueryDTO(BaseModel):
    """在线用户列表查询请求"""

    username: str | None = None
    page_num: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页条数")

    @field_validator("username", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)


class ForceOfflineDTO(BaseModel):
    """强制下线请求"""

    id: str = Field(description="在线会话 Key（访问令牌哈希前缀）")


class CpuInfoDTO(BaseModel):
    """CPU 信息"""

    coreCount: int = Field(description="逻辑核心数")
    usedPercent: float = Field(description="CPU 使用率（%）")


class MemoryInfoDTO(BaseModel):
    """内存信息（容量为格式化字符串，如 15.72 GB）"""

    total: str = Field(description="总内存")
    used: str = Field(description="已用内存")
    free: str = Field(description="可用内存")
    usedPercent: float = Field(description="使用率（%）")


class DiskInfoDTO(BaseModel):
    """磁盘信息"""

    total: str = Field(description="总容量")
    used: str = Field(description="已用容量")
    free: str = Field(description="可用容量")
    usedPercent: float = Field(description="使用率（%）")


class SystemInfoDTO(BaseModel):
    """系统基础信息"""

    hostname: str = Field(description="主机名")
    osName: str = Field(description="操作系统标识")
    osArch: str = Field(description="系统架构")
    pythonVersion: str = Field(description="Python 版本")
    workDir: str = Field(description="工作目录")
    bootTime: datetime = Field(description="系统启动时间")


class ProcessInfoDTO(BaseModel):
    """当前服务进程信息"""

    pid: int = Field(description="进程 ID")
    memoryUsed: str = Field(description="进程占用内存")
    cpuPercent: float = Field(description="进程 CPU 使用率（%）")
    runningTime: str = Field(description="进程运行时长")


class ServerInfoDTO(BaseModel):
    """服务器监控汇总响应（对标 RuoYi server monitor）"""

    cpu: CpuInfoDTO = Field(description="CPU 信息")
    memory: MemoryInfoDTO = Field(description="内存信息")
    disk: DiskInfoDTO = Field(description="磁盘信息")
    system: SystemInfoDTO = Field(description="系统信息")
    process: ProcessInfoDTO = Field(description="进程信息")


class CacheCommandStatDTO(BaseModel):
    """Redis 命令统计条目"""

    name: str = Field(description="命令名")
    calls: int = Field(description="调用次数")
    usec: int = Field(description="累计耗时（微秒）")


class CacheInfoDTO(BaseModel):
    """缓存监控响应（Redis info + 键统计）"""

    connected: bool = Field(description="Redis 是否可用")
    message: str = Field(default="", description="不可用原因说明")
    version: str | None = Field(default=None, description="Redis 版本")
    mode: str | None = Field(default=None, description="运行模式（standalone/cluster 等）")
    uptimeSeconds: int | None = Field(default=None, description="运行时长（秒）")
    usedMemory: str | None = Field(default=None, description="已用内存（human 格式）")
    usedMemoryPeak: str | None = Field(default=None, description="内存峰值（human 格式）")
    keyCount: int | None = Field(default=None, description="当前库键总数")
    hitRate: float | None = Field(default=None, description="命中率（%）")
    clients: int | None = Field(default=None, description="已连接客户端数")
    commandStats: list[CacheCommandStatDTO] = Field(default_factory=list, description="命令调用统计（Top10）")
