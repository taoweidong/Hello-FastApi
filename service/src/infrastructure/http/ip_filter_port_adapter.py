"""IP 过滤端口的适配器实现。

将基础设施层的 IPFilterCache 适配为领域层定义的 IPFilterPort 抽象接口。
遵循依赖倒置原则：应用层通过 IPFilterPort 抽象调用，不直接依赖基础设施层。
"""

from src.domain.services.cache_port import IPFilterPort
from src.infrastructure.logging.logger import logger


class IPFilterPortAdapter(IPFilterPort):
    """IPFilterPort 的适配器实现，委托给 IPFilterCache。"""

    async def refresh(self) -> None:
        """刷新 IP 过滤缓存。"""
        try:
            from src.infrastructure.http.ip_filter_cache import get_ip_filter_cache

            await get_ip_filter_cache().refresh()
        except Exception:
            logger.warning("刷新 IP 过滤缓存失败", exc_info=True)
