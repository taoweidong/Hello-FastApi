"""IP 规则缓存管理器。

协调 DB / Redis / app.state 三层缓存，提供 IP 黑白名单的加载与刷新。
遵循项目已有的模块级单例模式（_redis_manager, _db_manager）。
"""

from __future__ import annotations

from fastapi import FastAPI

from src.domain.entities.ip_rule import IPRuleEntity
from src.infrastructure.cache.cache_service import CacheService
from src.infrastructure.cache.redis_manager import get_redis
from src.infrastructure.database import get_db
from src.infrastructure.logging.logger import logger


class IPFilterCache:
    """IP 规则缓存管理器，协调 DB/Redis/app.state 三层缓存。"""

    def __init__(self) -> None:
        self._app: FastAPI | None = None
        self._cache_service: CacheService | None = None

    def set_app(self, app: FastAPI) -> None:
        """设置 FastAPI 应用实例引用，供后续 refresh 使用。"""
        self._app = app

    def _ensure_cache_service(self) -> CacheService:
        """确保 CacheService 实例可用。"""
        if self._cache_service is None:
            try:
                import asyncio

                redis_client = asyncio.get_event_loop().run_until_complete(get_redis())
                self._cache_service = CacheService(redis_client)
            except Exception:
                self._cache_service = CacheService(None)
        return self._cache_service

    async def _get_cache_service(self) -> CacheService:
        """异步获取 CacheService 实例。"""
        if self._cache_service is None:
            try:
                redis_client = await get_redis()
                self._cache_service = CacheService(redis_client)
            except Exception:
                logger.warning("获取 Redis 客户端失败，CacheService 降级为无缓存模式", exc_info=True)
                self._cache_service = CacheService(None)
        return self._cache_service

    async def load_to_app_state(self, app: FastAPI) -> None:
        """从数据库加载生效的 IP 规则到 app.state 和 Redis 缓存。

        在应用启动时（lifespan）调用一次。
        """
        self._app = app
        blacklist: set[str] = set()
        whitelist: set[str] = set()

        try:
            async for session in get_db():
                from src.infrastructure.repositories.ip_rule_repository import IPRuleRepository

                repo = IPRuleRepository(session)
                rules = await repo.get_effective_ip_rules()
                blacklist, whitelist = self._classify_rules(rules)

            logger.info(f"IP 规则加载完成: 黑名单 {len(blacklist)} 条, 白名单 {len(whitelist)} 条")
        except Exception:
            logger.warning("从数据库加载 IP 规则失败，将以空规则启动", exc_info=True)

        # 写入 app.state
        app.state.ip_blacklist = blacklist
        app.state.ip_whitelist = whitelist

        # 写入 Redis 缓存
        cache_service = await self._get_cache_service()
        await cache_service.set_ip_rules(blacklist, whitelist)

    async def refresh(self) -> None:
        """刷新 IP 规则缓存。

        在 IP 规则增删改后调用，重新从数据库加载到 app.state 和 Redis。
        """
        if self._app is None:
            logger.warning("IPFilterCache.refresh: app 未设置，跳过刷新")
            return

        try:
            async for session in get_db():
                from src.infrastructure.repositories.ip_rule_repository import IPRuleRepository

                repo = IPRuleRepository(session)
                rules = await repo.get_effective_ip_rules()
                blacklist, whitelist = self._classify_rules(rules)

            self._app.state.ip_blacklist = blacklist
            self._app.state.ip_whitelist = whitelist

            # 更新 Redis 缓存
            cache_service = await self._get_cache_service()
            await cache_service.set_ip_rules(blacklist, whitelist)

            logger.info(f"IP 规则缓存已刷新: 黑名单 {len(blacklist)} 条, 白名单 {len(whitelist)} 条")
        except Exception:
            logger.warning("刷新 IP 规则缓存失败", exc_info=True)

    @staticmethod
    def _classify_rules(rules: list[IPRuleEntity]) -> tuple[set[str], set[str]]:
        """将 IP 规则分类为黑名单和白名单集合。

        Returns:
            (blacklist, whitelist) 元组
        """
        blacklist: set[str] = set()
        whitelist: set[str] = set()
        for rule in rules:
            if rule.is_whitelist:
                whitelist.add(rule.ip_address)
            elif rule.is_blacklist:
                blacklist.add(rule.ip_address)
        return blacklist, whitelist


# ── 模块级单例 ──────────────────────────────────────────

_ip_filter_cache: IPFilterCache | None = None


def get_ip_filter_cache() -> IPFilterCache:
    """获取或创建 IPFilterCache 单例。"""
    global _ip_filter_cache
    if _ip_filter_cache is None:
        _ip_filter_cache = IPFilterCache()
    return _ip_filter_cache
