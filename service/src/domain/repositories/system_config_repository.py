"""系统配置仓储接口。

定义系统配置仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import SystemConfig


class SystemConfigRepositoryInterface(ABC):
    """系统配置的抽象仓储接口。"""

    @abstractmethod
    async def get_all(self, session: AsyncSession) -> list["SystemConfig"]:
        """获取所有配置。"""
        ...

    @abstractmethod
    async def get_by_id(self, config_id: str, session: AsyncSession) -> "SystemConfig | None":
        """根据 ID 获取配置。"""
        ...

    @abstractmethod
    async def get_by_key(self, key: str, session: AsyncSession) -> "SystemConfig | None":
        """根据 key 获取配置。"""
        ...

    @abstractmethod
    async def create(self, config: "SystemConfig", session: AsyncSession) -> "SystemConfig":
        """创建配置。"""
        ...

    @abstractmethod
    async def update(self, config: "SystemConfig", session: AsyncSession) -> "SystemConfig":
        """更新配置。"""
        ...

    @abstractmethod
    async def delete(self, config_id: str, session: AsyncSession) -> bool:
        """删除配置。"""
        ...
