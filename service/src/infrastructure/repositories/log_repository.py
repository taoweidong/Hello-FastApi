"""使用 SQLModel 和 FastCRUD 实现的日志仓库。

提供登录日志(sys_userloginlog)和统一操作日志(sys_logs)的数据库操作。
"""

from datetime import datetime

from fastcrud import FastCRUD
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.database.models import LoginLog, SystemLog


class LogRepository:
    """日志仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._login_log_crud = FastCRUD(LoginLog)
        self._system_log_crud = FastCRUD(SystemLog)

    # ============ 登录日志 (sys_userloginlog) ============

    async def get_login_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, status: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list[LoginLog], int]:
        """获取登录日志列表（支持筛选和分页）。"""
        query = select(LoginLog)
        count_query = select(sa_func.count()).select_from(LoginLog)

        if status is not None:
            query = query.where(LoginLog.status == status)
            count_query = count_query.where(LoginLog.status == status)
        if start_time:
            query = query.where(LoginLog.created_time >= start_time)
            count_query = count_query.where(LoginLog.created_time >= start_time)
        if end_time:
            query = query.where(LoginLog.created_time <= end_time)
            count_query = count_query.where(LoginLog.created_time <= end_time)

        query = query.order_by(LoginLog.created_time.desc())
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await session.exec(query)
        logs = list(result.all())

        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        return logs, total

    async def create_login_log(self, session: AsyncSession, log: LoginLog) -> LoginLog:
        """创建登录日志。"""
        return await self._login_log_crud.create(session, log)

    async def delete_login_logs(self, session: AsyncSession, log_ids: list[str]) -> int:
        """批量删除登录日志。"""
        count = 0
        for log_id in log_ids:
            log = await session.get(LoginLog, log_id)
            if log:
                await session.delete(log)
                count += 1
        await session.flush()
        return count

    async def clear_login_logs(self, session: AsyncSession) -> int:
        """清空所有登录日志。"""
        result = await session.exec(select(LoginLog))
        logs = result.all()
        count = len(logs)
        for log in logs:
            await session.delete(log)
        await session.flush()
        return count

    # ============ 统一操作日志 (sys_logs) ============

    async def get_operation_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, module: str | None = None, status_code: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list[SystemLog], int]:
        """获取操作日志列表（支持筛选和分页）。"""
        query = select(SystemLog)
        count_query = select(sa_func.count()).select_from(SystemLog)

        if module:
            query = query.where(SystemLog.module.contains(module))
            count_query = count_query.where(SystemLog.module.contains(module))
        if status_code is not None:
            query = query.where(SystemLog.status_code == status_code)
            count_query = count_query.where(SystemLog.status_code == status_code)
        if start_time:
            query = query.where(SystemLog.created_time >= start_time)
            count_query = count_query.where(SystemLog.created_time >= start_time)
        if end_time:
            query = query.where(SystemLog.created_time <= end_time)
            count_query = count_query.where(SystemLog.created_time <= end_time)

        query = query.order_by(SystemLog.created_time.desc())
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await session.exec(query)
        logs = list(result.all())

        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        return logs, total

    async def create_operation_log(self, session: AsyncSession, log: SystemLog) -> SystemLog:
        """创建操作日志。"""
        return await self._system_log_crud.create(session, log)

    async def get_operation_log_detail(self, session: AsyncSession, log_id: str) -> SystemLog | None:
        """获取操作日志详情。"""
        return await self._system_log_crud.get(session, id=log_id, schema_to_select=SystemLog, return_as_model=True)

    async def delete_operation_logs(self, session: AsyncSession, log_ids: list[str]) -> int:
        """批量删除操作日志。"""
        count = 0
        for log_id in log_ids:
            log = await session.get(SystemLog, log_id)
            if log:
                await session.delete(log)
                count += 1
        await session.flush()
        return count

    async def clear_operation_logs(self, session: AsyncSession) -> int:
        """清空所有操作日志。"""
        result = await session.exec(select(SystemLog))
        logs = result.all()
        count = len(logs)
        for log in logs:
            await session.delete(log)
        await session.flush()
        return count
