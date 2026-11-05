"""缓存端口工厂。

组合根按端口提供实例：读穿透类缓存聚合为 ``CachePort``（``CacheService`` 实现全部窄端口），
在线会话单独由 ``OnlineSessionStore`` 提供——两者的消费方注入方式相同（``Depends``）。
"""

from src.domain.services.cache_port import CachePort
from src.domain.services.online_session_port import OnlineSessionStore
from src.infrastructure.cache import CacheService, RedisOnlineSessionStore
from src.infrastructure.cache.redis_manager import get_redis

# 单例：Redis 客户端由 get_redis 自身缓存，这里保证组合根每次给出的端口实例身份稳定，
# 测试可用 dependency_overrides 精确替换。
_cache_service: CachePort | None = None

# 在线会话存储同样必须是单例：Redis 不可用时登录登记的会话只存在于进程内镜像，
# 每次新建实例会让监控查询读到空镜像（在线列表恒为空、强制下线失效）。
_session_store: OnlineSessionStore | None = None


async def get_cache_service() -> CachePort:
    """获取缓存服务单例实例。

    注入 Redis 客户端到 CacheService。Redis 不可用时 CacheService 降级为安全默认值。
    返回 CachePort 抽象类型，遵循依赖倒置原则；消费方按自己的用途声明更窄的端口类型。
    """
    global _cache_service
    if _cache_service is None:
        try:
            redis_client = await get_redis()
            _cache_service = CacheService(redis_client)
        except Exception:
            _cache_service = CacheService(None)
    return _cache_service


async def get_online_session_store() -> OnlineSessionStore:
    """获取在线会话存储单例（Redis 主存储 + 进程内镜像双写）。"""
    global _session_store
    if _session_store is None:
        try:
            redis_client = await get_redis()
            _session_store = RedisOnlineSessionStore(redis_client)
        except Exception:
            _session_store = RedisOnlineSessionStore(None)
    return _session_store
