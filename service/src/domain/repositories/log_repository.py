"""日志领域 - 仓储接口。

定义日志仓储的抽象接口，遵循依赖倒置原则。
"""

from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import LoginLog, OperationLog, SystemLog


class LogRepositoryInterface(Protocol):
    """日志仓储协议（实现类在 infrastructure 层）。"""

    async def get_login_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, username: str | None = None, status: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list["LoginLog"], int]: ...

    async def delete_login_logs(self, session: AsyncSession, log_ids: list[str]) -> int: ...

    async def clear_login_logs(self, session: AsyncSession) -> int: ...

    async def get_operation_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, module: str | None = None, status: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list["OperationLog"], int]: ...

    async def delete_operation_logs(self, session: AsyncSession, log_ids: list[str]) -> int: ...

    async def clear_operation_logs(self, session: AsyncSession) -> int: ...

    async def get_system_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, module: str | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list["SystemLog"], int]: ...

    async def get_system_log_detail(self, session: AsyncSession, log_id: str) -> "SystemLog | None": ...

    async def delete_system_logs(self, session: AsyncSession, log_ids: list[str]) -> int: ...

    async def clear_system_logs(self, session: AsyncSession) -> int: ...
