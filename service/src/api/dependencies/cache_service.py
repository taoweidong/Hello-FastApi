"""缓存服务工厂。"""

from src.domain.services.cache_port import CachePort
from src.infrastructure.cache import CacheService
from src.infrastructure.cache.redis_manager import get_redis

# 单例缓存服务：确保登录登记的在册会话与监控查询读取到同一内存镜像
# （Redis 不可用时内存降级依赖实例共享，每次新建将导致会话数据丢失）
_cache_service: CachePort | None = None


async def get_cache_service() -> CachePort:
    """获取缓存服务单例实例。

    注入 Redis 客户端到 CacheService。Redis 不可用时 CacheService 降级为安全默认值。
    返回 CachePort 抽象类型，遵循依赖倒置原则。
    """
    global _cache_service
    if _cache_service is None:
        try:
            redis_client = await get_redis()
            _cache_service = CacheService(redis_client)
        except Exception:
            _cache_service = CacheService(None)
    return _cache_service
