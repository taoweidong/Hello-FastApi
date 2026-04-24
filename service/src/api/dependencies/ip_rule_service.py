"""IP 规则应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.ip_rule_service import IPRuleService
from src.domain.services.cache_port import IPFilterPort
from src.domain.services.logging_port import LoggingPort
from src.infrastructure.database import get_db
from src.infrastructure.http.ip_filter_port_adapter import IPFilterPortAdapter
from src.infrastructure.logging.logging_adapter import logging_adapter
from src.infrastructure.repositories.ip_rule_repository import IPRuleRepository


def _get_ip_filter_port() -> IPFilterPort:
    """获取 IP 过滤端口实例。"""
    return IPFilterPortAdapter()


def _get_logging_port() -> LoggingPort:
    """获取日志端口实例。"""
    return logging_adapter


async def get_ip_rule_service(
    db: AsyncSession = Depends(get_db),
    ip_filter_port: IPFilterPort = Depends(_get_ip_filter_port),
    logging_port: LoggingPort = Depends(_get_logging_port),
) -> IPRuleService:
    """获取 IP 规则服务实例。

    注入 IP 规则仓储、IP 过滤端口和日志端口依赖。
    """
    ip_rule_repo = IPRuleRepository(db)
    return IPRuleService(ip_rule_repo=ip_rule_repo, ip_filter_port=ip_filter_port, logging_port=logging_port)
