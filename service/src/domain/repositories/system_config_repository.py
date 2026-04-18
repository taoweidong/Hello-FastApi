"""系统配置仓储接口。

定义系统配置仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.entities.system_config import SystemConfigEntity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class SystemConfigRepositoryInterface(ABC):
    """系统配置的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        """初始化仓储，注入数据库会话。"""
        ...

    @abstractmethod
    async def get_all(self, page_num: int = 1, page_size: int = 10, key: str | None = None, is_active: int | None = None) -> list[SystemConfigEntity]:
        """获取配置列表（支持分页和筛选）。"""
        ...

    @abstractmethod
    async def count(self, key: str | None = None, is_active: int | None = None) -> int:
        """统计配置数量（支持筛选）。"""
        ...

    @abstractmethod
    async def get_by_id(self, config_id: str) -> SystemConfigEntity | None:
        """根据 ID 获取配置。"""
        ...

    @abstractmethod
    async def get_by_key(self, key: str) -> SystemConfigEntity | None:
        """根据 key 获取配置。"""
        ...

    @abstractmethod
    async def create(self, config: SystemConfigEntity) -> SystemConfigEntity:
        """创建配置。"""
        ...

    @abstractmethod
    async def update(self, config: SystemConfigEntity) -> SystemConfigEntity:
        """更新配置。"""
        ...

    @abstractmethod
    async def delete(self, config_id: str) -> bool:
        """删除配置。"""
        ...
