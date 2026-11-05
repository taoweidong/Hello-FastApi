"""在线用户会话存储。

实现领域端口 ``OnlineSessionStore``：Redis 为主存储，进程内字典为镜像。
双写而非只写 Redis 的原因：Redis 未配置或不可用时，监控页仍需列出本机签发的会话，
镜像同时充当降级数据源——因此本组件必须以**单例**注入，
每次请求新建实例会让登录登记与在线查询读到不同的镜像。
"""

import json
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

from src.domain.services.online_session_port import OnlineSessionStore
from src.infrastructure.cache.ttl import remaining_seconds
from src.infrastructure.logging.logger import logger


class RedisOnlineSessionStore(OnlineSessionStore):
    """Redis + 进程内镜像双写的在线会话存储。"""

    # Key 前缀
    _ONLINE_USER_PREFIX = "online:user:"

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis = redis_client
        # 在线会话内存镜像存储（Redis 未配置/不可用时降级数据源）
        # key: 会话 Key，value: {"info": 会话信息字典, "expires_at": 过期时间 UTC}
        self._memory: dict[str, dict] = {}

    async def set_online_user(self, session_key: str, info: dict[str, Any], expires_at: datetime) -> bool:
        """登记在线用户会话（Redis 主存储 + 内存镜像双写）。

        Redis 未配置或不可用时自动降级为内存存储，保证在线用户功能可用；
        内存条目同样遵循 TTL 约束，读取时惰性清理已过期会话。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）
            info: 会话信息字典
            expires_at: 会话过期时间（TTL 与访问令牌生命周期一致）

        Returns:
            是否成功写入缓存
        """
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        ttl = remaining_seconds(expires_at)
        if ttl <= 0:
            # Token 已过期，无需登记
            self._memory.pop(session_key, None)
            return True
        # 内存镜像总是写入，Redis 异常时不阻塞在线用户功能
        self._memory[session_key] = {"info": info, "expires_at": expires_at}
        if self._redis is None:
            return True
        try:
            await self._redis.set(
                f"{self._ONLINE_USER_PREFIX}{session_key}", json.dumps(info, ensure_ascii=False), ex=ttl
            )
            return True
        except Exception:
            logger.warning("Redis 登记在线用户会话失败，已降级为内存存储", exc_info=True)
            return True

    async def get_online_user(self, session_key: str) -> dict[str, Any] | None:
        """获取在线用户会话（Redis 优先，未命中或不可用时读内存镜像）。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）

        Returns:
            会话信息字典（命中时），None 表示未命中
        """
        if self._redis is not None:
            try:
                data = await self._redis.get(f"{self._ONLINE_USER_PREFIX}{session_key}")
                if data is not None:
                    return json.loads(data)
            except Exception:
                logger.warning(f"Redis 读取在线用户会话失败: {session_key}", exc_info=True)
        return self._memory_get_online(session_key)

    async def get_online_users(self) -> list[dict[str, Any]]:
        """获取全部在线用户会话（Redis 优先，不可用时降级内存镜像）。

        Returns:
            会话信息字典列表（每项含 id=session_key 供强制下线使用）；
            Redis 不可用时返回内存镜像中未过期的会话
        """
        if self._redis is not None:
            try:
                sessions: list[dict] = []
                prefix = self._ONLINE_USER_PREFIX
                async for key in self._redis.scan_iter(match=f"{prefix}*", count=100):
                    data = await self._redis.get(key)
                    if data is None:
                        continue
                    item = json.loads(data)
                    item["id"] = key[len(prefix) :]
                    sessions.append(item)
                return sessions
            except Exception:
                logger.warning("Redis 遍历在线用户会话失败，降级读取内存镜像", exc_info=True)
        return self._memory_get_all_online()

    async def delete_online_user(self, session_key: str) -> bool:
        """删除在线用户会话（强制下线），同步清理 Redis 与内存镜像。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）

        Returns:
            是否成功删除
        """
        self._memory.pop(session_key, None)
        if self._redis is None:
            return True
        try:
            await self._redis.delete(f"{self._ONLINE_USER_PREFIX}{session_key}")
            return True
        except Exception:
            logger.warning("Redis 删除在线用户会话失败", exc_info=True)
            return False

    # ---- 内存镜像读取（惰性清理过期条目） ----

    def _memory_get_online(self, session_key: str) -> dict | None:
        """从内存镜像读取在线会话（惰性清理已过期条目）。"""
        entry = self._memory.get(session_key)
        if entry is None:
            return None
        if entry["expires_at"] <= datetime.now(timezone.utc):
            self._memory.pop(session_key, None)
            return None
        return dict(entry["info"])

    def _memory_get_all_online(self) -> list[dict]:
        """从内存镜像获取全部在线会话（过滤并清理已过期条目）。"""
        now = datetime.now(timezone.utc)
        for key in list(self._memory):
            if self._memory[key]["expires_at"] <= now:
                self._memory.pop(key, None)
        return [{**entry["info"], "id": key} for key, entry in self._memory.items()]
