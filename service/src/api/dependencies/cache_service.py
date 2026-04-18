"""缓存服务工厂。"""

from src.domain.services.cache_port import CachePort
from src.infrastructure.cache import CacheService
from src.infrastructure.cache.redis_manager import get_redis


async def get_cache_service() -> CachePort:
    """获取缓存服务实例。

    注入 Redis 客户端到 CacheService。Redis 不可用时 CacheService 降级为安全默认值。
    返回 CachePort 抽象类型，遵循依赖倒置原则。
    """
    try:
        redis_client = await get_redis()
        return CacheService(redis_client)
    except Exception:
        return CacheService(None)
