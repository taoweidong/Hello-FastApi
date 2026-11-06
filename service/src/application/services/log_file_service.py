"""应用层 - 日志文件浏览服务。

供管理员远程排查问题：列出日志目录文件、尾部读取、定位文件路径。
替代"登录服务器看日志"的运维路径；访问控制由路由层
``require_superuser`` 强制（日志含敏感信息，不得匿名或放宽）。

安全约束：
- 文件名只允许 ``[A-Za-z0-9._-]``，禁止任何路径分隔符与 ``..``；
- 解析后的绝对路径必须落在日志目录内（防符号链接/穿越逃逸）；
- 尾读行数有硬上限，防止一次请求拖回超大文件。
"""

import asyncio
import time
from pathlib import Path

from src.application.dto.monitor_dto import LogFileInfoDTO

# 文件名字符合法白名单：字母/数字/点/下划线/连字符（日志与轮转/压缩产物均满足）
_SAFE_FILENAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")

# 尾读行数上限：防止超大响应拖垮网关与前端
MAX_TAIL_LINES = 1000

# 尾读时从文件末尾按块回扫的块大小（64KB 足以覆盖长日志行）
_TAIL_CHUNK_SIZE = 65536


class LogFileNotFoundError(Exception):
    """请求的日志文件不存在。"""


class LogFileService:
    """日志目录的只读浏览服务。"""

    def __init__(self, logs_dir: Path | str):
        self._logs_dir = Path(logs_dir)

    @property
    def logs_dir(self) -> Path:
        return self._logs_dir

    def _resolve(self, filename: str) -> Path:
        """校验并解析文件名到日志目录内的绝对路径。

        Raises:
            ValueError: 文件名含非法字符或解析后逃逸出日志目录时抛出。
            LogFileNotFoundError: 文件不存在或不是普通文件时抛出。
        """
        if not filename or set(filename) - _SAFE_FILENAME_CHARS:
            raise ValueError("非法的日志文件名")
        candidate = (self._logs_dir / filename).resolve()
        try:
            candidate.relative_to(self._logs_dir.resolve())
        except ValueError as exc:
            raise ValueError("非法的日志文件路径") from exc
        if not candidate.is_file():
            raise LogFileNotFoundError(f"日志文件不存在: {filename}")
        return candidate

    async def list_files(self) -> list[LogFileInfoDTO]:
        """列出日志目录下的全部普通文件（按修改时间倒序）。"""
        return await asyncio.to_thread(self._list_files_sync)

    def _list_files_sync(self) -> list[LogFileInfoDTO]:
        entries: list[LogFileInfoDTO] = []
        try:
            children = list(self._logs_dir.iterdir())
        except FileNotFoundError:
            return []
        for path in children:
            try:
                if not path.is_file():
                    continue
                stat = path.stat()
            except OSError:
                continue
            entries.append(
                LogFileInfoDTO(
                    name=path.name,
                    sizeBytes=stat.st_size,
                    modifiedTime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                )
            )
        entries.sort(key=lambda e: e.modifiedTime, reverse=True)
        return entries

    async def tail(self, filename: str, lines: int = 200) -> str:
        """读取文件末尾 N 行（默认 200，上限 1000）。

        从文件末尾按块回扫，避免整读大文件。
        """
        lines = max(1, min(int(lines), MAX_TAIL_LINES))
        path = await asyncio.to_thread(self._resolve, filename)
        return await asyncio.to_thread(self._tail_sync, path, lines)

    @staticmethod
    def _tail_sync(path: Path, lines: int) -> str:
        size = path.stat().st_size
        if size == 0:
            return ""
        with open(path, "rb") as f:
            # 从末尾按块回扫，直到凑够目标行数或到达文件头
            remaining_lines = lines
            buffer = b""
            position = size
            while position > 0 and remaining_lines > 0:
                chunk_size = min(_TAIL_CHUNK_SIZE, position)
                position -= chunk_size
                f.seek(position)
                buffer = f.read(chunk_size) + buffer
                remaining_lines = lines - buffer.count(b"\n")
            text = buffer.decode("utf-8", errors="replace")
        tail_lines = text.splitlines()[-lines:]
        return "\n".join(tail_lines)

    async def open_path(self, filename: str) -> Path:
        """校验并返回可交给 FileResponse 的文件路径。"""
        return await asyncio.to_thread(self._resolve, filename)

    @staticmethod
    def human_size(size_bytes: int) -> str:
        """字节转可读大小（前端展示兜底，主要在前端格式化）。"""
        size = float(size_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
            size /= 1024
        return f"{size:.1f} TB"
