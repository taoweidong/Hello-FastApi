"""使用 SQLModel 原生 API 实现的日志仓库。

提供登录日志(sys_userloginlog)和统一操作日志(sys_logs)的数据库操作。
"""

from datetime import datetime

from sqlalchemy import delete as sa_delete
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.log import LoginLogEntity, OperationLogEntity
from src.domain.repositories.log_repository import LogRepositoryInterface
from src.infrastructure.database.models import LoginLog, SystemLog


class LogRepository(LogRepositoryInterface):
    """日志仓储的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ============ 登录日志 (sys_userloginlog) ============

    async def get_login_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        status: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[LoginLogEntity], int]:
        """获取登录日志列表（支持筛选和分页）。"""
        stmt = select(LoginLog).order_by(LoginLog.created_time.desc())
        count_stmt = select(sa_func.count()).select_from(LoginLog)

        if status is not None:
            stmt = stmt.where(LoginLog.status == status)
            count_stmt = count_stmt.where(LoginLog.status == status)
        if start_time:
            stmt = stmt.where(LoginLog.created_time >= start_time)
            count_stmt = count_stmt.where(LoginLog.created_time >= start_time)
        if end_time:
            stmt = stmt.where(LoginLog.created_time <= end_time)
            count_stmt = count_stmt.where(LoginLog.created_time <= end_time)

        offset = (page_num - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.exec(stmt)
        logs = list(result.all())

        total_result = await self.session.exec(count_stmt)
        total = total_result.one()

        return [log.to_domain() for log in logs], total

    async def create_login_log(self, log: LoginLogEntity) -> LoginLogEntity:
        """创建登录日志。"""
        model = LoginLog.from_domain(log)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        loaded = await self.session.get(LoginLog, model.id)
        return loaded.to_domain()  # type: ignore[union-attr]

    async def delete_login_logs(self, log_ids: list[str]) -> int:
        """批量删除登录日志。"""
        if not log_ids:
            return 0
        stmt = sa_delete(LoginLog).where(LoginLog.id.in_(log_ids))
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount or 0

    async def clear_login_logs(self) -> int:
        """清空所有登录日志。"""
        count_result = await self.session.exec(select(sa_func.count()).select_from(LoginLog))
        total = count_result.one()
        stmt = sa_delete(LoginLog)
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return total

    # ============ 统一操作日志 (sys_logs) ============

    async def get_operation_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        """获取操作日志列表（支持筛选和分页）。"""
        stmt = select(SystemLog).order_by(SystemLog.created_time.desc())
        count_stmt = select(sa_func.count()).select_from(SystemLog)

        if module:
            stmt = stmt.where(SystemLog.module.contains(module))
            count_stmt = count_stmt.where(SystemLog.module.contains(module))
        if status_code is not None:
            stmt = stmt.where(SystemLog.status_code == status_code)
            count_stmt = count_stmt.where(SystemLog.status_code == status_code)
        if start_time:
            stmt = stmt.where(SystemLog.created_time >= start_time)
            count_stmt = count_stmt.where(SystemLog.created_time >= start_time)
        if end_time:
            stmt = stmt.where(SystemLog.created_time <= end_time)
            count_stmt = count_stmt.where(SystemLog.created_time <= end_time)

        offset = (page_num - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.exec(stmt)
        logs = list(result.all())

        total_result = await self.session.exec(count_stmt)
        total = total_result.one()

        return [log.to_domain() for log in logs], total

    async def create_operation_log(self, log: OperationLogEntity) -> OperationLogEntity:
        """创建操作日志。"""
        model = SystemLog.from_domain(log)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        loaded = await self.session.get(SystemLog, model.id)
        return loaded.to_domain()  # type: ignore[union-attr]

    async def get_operation_log_detail(self, log_id: str) -> OperationLogEntity | None:
        """获取操作日志详情。"""
        stmt = select(SystemLog).where(SystemLog.id == log_id)
        result = await self.session.exec(stmt)
        model = result.first()
        return model.to_domain() if model else None

    async def delete_operation_logs(self, log_ids: list[str]) -> int:
        """批量删除操作日志。"""
        if not log_ids:
            return 0
        stmt = sa_delete(SystemLog).where(SystemLog.id.in_(log_ids))
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount or 0

    async def clear_operation_logs(self) -> int:
        """清空所有操作日志。"""
        count_result = await self.session.exec(select(sa_func.count()).select_from(SystemLog))
        total = count_result.one()
        stmt = sa_delete(SystemLog)
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return total

    # ============ 系统日志（与操作日志共享 sys_logs 表） ============

    async def get_system_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        """获取系统日志列表。与操作日志共享同一张表。"""
        return await self.get_operation_logs(page_num, page_size, module, status_code, start_time, end_time)

    async def get_system_log_detail(self, log_id: str) -> OperationLogEntity | None:
        """获取系统日志详情。"""
        return await self.get_operation_log_detail(log_id)
