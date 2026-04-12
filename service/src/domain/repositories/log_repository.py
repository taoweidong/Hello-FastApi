"""日志领域 - 仓储接口。

定义日志仓储的抽象接口，遵循依赖倒置原则。
"""

from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import LoginLog, SystemLog


class LogRepositoryInterface(Protocol):
    """日志仓储协议（实现类在 infrastructure 层）。"""

    # 登录日志
    async def get_login_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, status: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list["LoginLog"], int]: ...

    async def create_login_log(self, session: AsyncSession, log: "LoginLog") -> "LoginLog": ...

    async def delete_login_logs(self, session: AsyncSession, log_ids: list[str]) -> int: ...

    async def clear_login_logs(self, session: AsyncSession) -> int: ...

    # 统一操作日志(sys_logs)
    async def get_operation_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, module: str | None = None, status_code: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list["SystemLog"], int]: ...

    async def create_operation_log(self, session: AsyncSession, log: "SystemLog") -> "SystemLog": ...

    async def get_operation_log_detail(self, session: AsyncSession, log_id: str) -> "SystemLog | None": ...

    async def delete_operation_logs(self, session: AsyncSession, log_ids: list[str]) -> int: ...

    async def clear_operation_logs(self, session: AsyncSession) -> int: ...
