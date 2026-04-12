"""使用 SQLModel 和 FastCRUD 实现的 IP 规则仓库。

提供 IP 黑白名单规则(sys_ip_rules)的数据库操作。
"""

from datetime import datetime

from fastcrud import FastCRUD
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.database.models import IPRule


class IPRuleRepository:
    """IP 规则仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(IPRule)

    async def get_ip_rules(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, rule_type: str | None = None, is_active: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list[IPRule], int]:
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

        result = await session.exec(query)
        rules = list(result.all())

        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        return rules, total

    async def get_ip_rule_by_id(self, session: AsyncSession, rule_id: str) -> IPRule | None:
        """根据 ID 获取 IP 规则。"""
        return await session.get(IPRule, rule_id)

    async def create_ip_rule(self, session: AsyncSession, rule: IPRule) -> IPRule:
        """创建 IP 规则。"""
        return await self._crud.create(session, rule)

    async def update_ip_rule(self, session: AsyncSession, rule: IPRule) -> IPRule:
        """更新 IP 规则。"""
        session.add(rule)
        await session.flush()
        return rule

    async def delete_ip_rules(self, session: AsyncSession, rule_ids: list[str]) -> int:
        """批量删除 IP 规则。"""
        count = 0
        for rule_id in rule_ids:
            rule = await session.get(IPRule, rule_id)
            if rule:
                await session.delete(rule)
                count += 1
        await session.flush()
        return count

    async def clear_ip_rules(self, session: AsyncSession) -> int:
        """清空所有 IP 规则。"""
        result = await session.exec(select(IPRule))
        rules = result.all()
        count = len(rules)
        for rule in rules:
            await session.delete(rule)
        await session.flush()
        return count
