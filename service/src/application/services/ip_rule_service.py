"""应用层 - IP 规则服务。

提供 IP 黑白名单规则的业务逻辑。
"""

from datetime import datetime

from src.domain.entities.ip_rule import IPRuleEntity
from src.domain.exceptions import NotFoundError
from src.domain.repositories.ip_rule_repository import IPRuleRepositoryInterface
from src.domain.services.cache_port import IPFilterPort
from src.domain.services.logging_port import LoggingPort


def _parse_time_bound(value: object) -> datetime | None:
    """解析时间边界值。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.fromisoformat(s)
        except ValueError:
            return None
    return None


class IPRuleService:
    """IP 规则领域操作的应用服务。"""

    def __init__(
        self,
        ip_rule_repo: IPRuleRepositoryInterface,
        ip_filter_port: IPFilterPort | None = None,
        logging_port: LoggingPort | None = None,
    ):
        self.ip_rule_repo = ip_rule_repo
        self.ip_filter_port = ip_filter_port
        self.logging_port = logging_port

    async def get_ip_rules(
        self,
        page_num: int = 1,
        page_size: int = 10,
        rule_type: str | None = None,
        is_active: int | None = None,
        created_time: str | list | None = None,
    ) -> tuple[list, int]:
        """获取 IP 规则列表。"""
        start_time = None
        end_time = None
        if created_time and isinstance(created_time, list) and len(created_time) == 2:
            start_time = _parse_time_bound(created_time[0])
            end_time = _parse_time_bound(created_time[1])

        return await self.ip_rule_repo.get_ip_rules(
            page_num=page_num,
            page_size=page_size,
            rule_type=rule_type,
            is_active=is_active,
            start_time=start_time,
            end_time=end_time,
        )

    async def get_ip_rule(self, rule_id: str) -> IPRuleEntity:
        """获取单个 IP 规则。"""
        rule = await self.ip_rule_repo.get_ip_rule_by_id(rule_id=rule_id)
        if rule is None:
            raise NotFoundError("IP规则不存在")
        return rule

    async def create_ip_rule(
        self,
        ip_address: str,
        rule_type: str,
        reason: str | None = None,
        is_active: int = 1,
        expires_at: datetime | None = None,
    ) -> IPRuleEntity:
        """创建 IP 规则。"""
        entity = IPRuleEntity.create_new(
            ip_address=ip_address, rule_type=rule_type, reason=reason, is_active=is_active, expires_at=expires_at
        )
        result = await self.ip_rule_repo.create_ip_rule(entity)
        await self._refresh_ip_filter_cache()
        return result

    async def update_ip_rule(
        self,
        rule_id: str,
        ip_address: str | None = None,
        rule_type: str | None = None,
        reason: str | None = None,
        is_active: int | None = None,
        expires_at: datetime | None = None,
        description: str | None = None,
    ) -> IPRuleEntity:
        """更新 IP 规则。"""
        rule = await self.ip_rule_repo.get_ip_rule_by_id(rule_id=rule_id)
        if rule is None:
            raise NotFoundError("IP规则不存在")

        rule.update_info(
            ip_address=ip_address,
            rule_type=rule_type,
            reason=reason,
            is_active=is_active,
            expires_at=expires_at,
            description=description,
        )
        result = await self.ip_rule_repo.update_ip_rule(rule)
        await self._refresh_ip_filter_cache()
        return result

    async def delete_ip_rules(self, rule_ids: list[str]) -> int:
        """批量删除 IP 规则。"""
        result = await self.ip_rule_repo.delete_ip_rules(rule_ids=rule_ids)
        await self._refresh_ip_filter_cache()
        return result

    async def clear_ip_rules(self) -> int:
        """清空所有 IP 规则。"""
        result = await self.ip_rule_repo.clear_ip_rules()
        await self._refresh_ip_filter_cache()
        return result

    async def _refresh_ip_filter_cache(self) -> None:
        """刷新 IP 过滤缓存。"""
        if self.ip_filter_port is None:
            return
        try:
            await self.ip_filter_port.refresh()
        except Exception:
            if self.logging_port:
                self.logging_port.warning("刷新 IP 过滤缓存失败", exc_info=True)
