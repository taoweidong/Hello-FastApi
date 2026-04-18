"""IP 规则领域 - 仓储接口。

定义 IP 规则仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from src.domain.entities.ip_rule import IPRuleEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class IPRuleRepositoryInterface(ABC):
    """IP 规则的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_ip_rules(self, page_num: int = 1, page_size: int = 10, rule_type: str | None = None, is_active: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list[IPRuleEntity], int]:
        """获取 IP 规则列表。"""
        ...

    @abstractmethod
    async def get_ip_rule_by_id(self, rule_id: str) -> IPRuleEntity | None:
        """根据 ID 获取 IP 规则。"""
        ...

    @abstractmethod
    async def create_ip_rule(self, rule: IPRuleEntity) -> IPRuleEntity:
        """创建 IP 规则。"""
        ...

    @abstractmethod
    async def update_ip_rule(self, rule: IPRuleEntity) -> IPRuleEntity:
        """更新 IP 规则。"""
        ...

    @abstractmethod
    async def delete_ip_rules(self, rule_ids: list[str]) -> int:
        """删除 IP 规则。"""
        ...

    @abstractmethod
    async def clear_ip_rules(self) -> int:
        """清空 IP 规则。"""
        ...
