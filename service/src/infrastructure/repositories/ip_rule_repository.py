"""使用 SQLModel 和 FastCRUD 实现的 IP 规则仓库。

提供 IP 黑白名单规则(sys_ip_rules)的数据库操作。
"""

from datetime import datetime

from fastcrud import FastCRUD
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.ip_rule import IPRuleEntity
from src.domain.repositories.ip_rule_repository import IPRuleRepositoryInterface
from src.infrastructure.database.models import IPRule


class IPRuleRepository(IPRuleRepositoryInterface):
    """IP 规则仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(IPRule)

    async def get_ip_rules(
        self,
        page_num: int = 1,
        page_size: int = 10,
        rule_type: str | None = None,
        is_active: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[IPRuleEntity], int]:
        """获取 IP 规则列表（支持筛选和分页）。"""
        query = select(IPRule)
        count_query = select(sa_func.count()).select_from(IPRule)

        if rule_type:
            query = query.where(IPRule.rule_type == rule_type)
            count_query = count_query.where(IPRule.rule_type == rule_type)
        if is_active is not None:
            query = query.where(IPRule.is_active == is_active)
            count_query = count_query.where(IPRule.is_active == is_active)
        if start_time:
            query = query.where(IPRule.created_time >= start_time)
            count_query = count_query.where(IPRule.created_time >= start_time)
        if end_time:
            query = query.where(IPRule.created_time <= end_time)
            count_query = count_query.where(IPRule.created_time <= end_time)

        query = query.order_by(IPRule.created_time.desc())
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.exec(query)
        rules = list(result.all())

        total_result = await self.session.exec(count_query)
        total = total_result.one()

        return [rule.to_domain() for rule in rules], total

    async def get_ip_rule_by_id(self, rule_id: str) -> IPRuleEntity | None:
        """根据 ID 获取 IP 规则。"""
        model = await self._crud.get(self.session, id=rule_id, schema_to_select=IPRule, return_as_model=True)
        return model.to_domain() if model else None

    async def create_ip_rule(self, rule: IPRuleEntity) -> IPRuleEntity:
        """创建 IP 规则。"""
        model = IPRule.from_domain(rule)
        self.session.add(model)
        await self.session.flush()
        # 读回以获取自动生成的字段
        loaded = await self.get_ip_rule_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update_ip_rule(self, rule: IPRuleEntity) -> IPRuleEntity:
        """更新 IP 规则。"""
        from sqlalchemy import update as sa_update

        stmt = (
            sa_update(IPRule)
            .where(IPRule.id == rule.id)
            .values(
                ip_address=rule.ip_address,
                rule_type=rule.rule_type,
                reason=rule.reason,
                is_active=rule.is_active,
                creator_id=rule.creator_id,
                modifier_id=rule.modifier_id,
                expires_at=rule.expires_at,
                description=rule.description,
            )
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_ip_rule_by_id(rule.id)
        return updated  # type: ignore[return-value]

    async def delete_ip_rules(self, rule_ids: list[str]) -> int:
        """批量删除 IP 规则。"""
        if not rule_ids:
            return 0
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(IPRule).where(IPRule.id.in_(rule_ids))
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount or 0

    async def clear_ip_rules(self) -> int:
        """清空所有 IP 规则。"""
        from sqlalchemy import delete as sa_delete

        count_result = await self.session.exec(select(sa_func.count()).select_from(IPRule))
        total = count_result.one()
        stmt = sa_delete(IPRule)
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return total

    async def get_effective_ip_rules(self) -> list[IPRuleEntity]:
        """获取所有生效的 IP 规则（is_active=1 且未过期）。"""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        query = select(IPRule).where(
            IPRule.is_active == 1,
            (IPRule.expires_at.is_(None)) | (IPRule.expires_at > now),  # type: ignore[union-attr]
        )
        result = await self.session.exec(query)
        return [rule.to_domain() for rule in result.all()]
