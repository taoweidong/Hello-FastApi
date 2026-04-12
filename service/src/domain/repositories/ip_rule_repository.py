"""IP 规则领域 - 仓储接口。

定义 IP 规则仓储的抽象接口，遵循依赖倒置原则。
"""

from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import IPRule


class IPRuleRepositoryInterface(Protocol):
    """IP 规则仓储协议（实现类在 infrastructure 层）。"""

    async def get_ip_rules(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, rule_type: str | None = None, is_active: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list["IPRule"], int]: ...

    async def get_ip_rule_by_id(self, session: AsyncSession, rule_id: str) -> "IPRule | None": ...

    async def create_ip_rule(self, session: AsyncSession, rule: "IPRule") -> "IPRule": ...

    async def update_ip_rule(self, session: AsyncSession, rule: "IPRule") -> "IPRule": ...

    async def delete_ip_rules(self, session: AsyncSession, rule_ids: list[str]) -> int: ...

    async def clear_ip_rules(self, session: AsyncSession) -> int: ...
