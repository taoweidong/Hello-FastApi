"""日志应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.log_service import LogService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.log_repository import LogRepository


async def get_log_service(db: AsyncSession = Depends(get_db)) -> LogService:
    """获取日志服务实例。

    注入日志仓储依赖。
    """
    log_repo = LogRepository(db)
    return LogService(log_repo=log_repo)
