"""IP 规则应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.ip_rule_service import IPRuleService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.ip_rule_repository import IPRuleRepository


async def get_ip_rule_service(db: AsyncSession = Depends(get_db)) -> IPRuleService:
    """获取 IP 规则服务实例。

    注入 IP 规则仓储依赖。
    """
    ip_rule_repo = IPRuleRepository(db)
    return IPRuleService(session=db, ip_rule_repo=ip_rule_repo)
