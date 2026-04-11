"""使用 SQLModel 和 FastCRUD 实现的日志仓库。

提供登录日志、操作日志、系统日志的数据库操作。
"""

from datetime import datetime

from fastcrud import FastCRUD
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.database.models import LoginLog, OperationLog, SystemLog


class LogRepository:
    """日志仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        """初始化日志仓储。

        Args:
            session: 数据库会话
        """
        self.session = session
        self._login_log_crud = FastCRUD(LoginLog)
        self._operation_log_crud = FastCRUD(OperationLog)
        self._system_log_crud = FastCRUD(SystemLog)

    # ============ 登录日志 ============

    async def get_login_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, username: str | None = None, status: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list[LoginLog], int]:
        """获取登录日志列表（支持筛选和分页）。

        Args:
            session: 数据库会话
            page_num: 页码，从1开始
            page_size: 每页数量
            username: 用户名模糊查询
            status: 登录状态
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            (日志列表, 总数) 元组
        """
        query = select(LoginLog)
        count_query = select(sa_func.count()).select_from(LoginLog)

        # 应用筛选条件
        if username:
            query = query.where(LoginLog.username.contains(username))
            count_query = count_query.where(LoginLog.username.contains(username))
        if status is not None:
            query = query.where(LoginLog.status == status)
            count_query = count_query.where(LoginLog.status == status)
        if start_time:
            query = query.where(LoginLog.login_time >= start_time)
            count_query = count_query.where(LoginLog.login_time >= start_time)
        if end_time:
            query = query.where(LoginLog.login_time <= end_time)
            count_query = count_query.where(LoginLog.login_time <= end_time)

        # 按时间倒序
        query = query.order_by(LoginLog.login_time.desc())

        # 分页
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await session.exec(query)
        logs = list(result.all())

        # 获取总数
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        return logs, total

    async def delete_login_logs(self, session: AsyncSession, log_ids: list[str]) -> int:
        """批量删除登录日志。

        Args:
            session: 数据库会话
            log_ids: 日志ID列表

        Returns:
            删除的数量
        """
        count = 0
        for log_id in log_ids:
            log = await session.get(LoginLog, log_id)
            if log:
                await session.delete(log)
                count += 1
        await session.flush()
        return count

    async def clear_login_logs(self, session: AsyncSession) -> int:
        """清空所有登录日志。

        Args:
            session: 数据库会话

        Returns:
            删除的数量
        """
        result = await session.exec(select(LoginLog))
        logs = result.all()
        count = len(logs)
        for log in logs:
            await session.delete(log)
        await session.flush()
        return count

    # ============ 操作日志 ============

    async def get_operation_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, module: str | None = None, status: int | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list[OperationLog], int]:
        """获取操作日志列表（支持筛选和分页）。

        Args:
            session: 数据库会话
            page_num: 页码，从1开始
            page_size: 每页数量
            module: 模块名称模糊查询
            status: 操作状态
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            (日志列表, 总数) 元组
        """
        query = select(OperationLog)
        count_query = select(sa_func.count()).select_from(OperationLog)

        # 应用筛选条件
        if module:
            query = query.where(OperationLog.module.contains(module))
            count_query = count_query.where(OperationLog.module.contains(module))
        if status is not None:
            query = query.where(OperationLog.status == status)
            count_query = count_query.where(OperationLog.status == status)
        if start_time:
            query = query.where(OperationLog.operating_time >= start_time)
            count_query = count_query.where(OperationLog.operating_time >= start_time)
        if end_time:
            query = query.where(OperationLog.operating_time <= end_time)
            count_query = count_query.where(OperationLog.operating_time <= end_time)

        # 按时间倒序
        query = query.order_by(OperationLog.operating_time.desc())

        # 分页
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await session.exec(query)
        logs = list(result.all())

        # 获取总数
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        return logs, total

    async def delete_operation_logs(self, session: AsyncSession, log_ids: list[str]) -> int:
        """批量删除操作日志。

        Args:
            session: 数据库会话
            log_ids: 日志ID列表

        Returns:
            删除的数量
        """
        count = 0
        for log_id in log_ids:
            log = await session.get(OperationLog, log_id)
            if log:
                await session.delete(log)
                count += 1
        await session.flush()
        return count

    async def clear_operation_logs(self, session: AsyncSession) -> int:
        """清空所有操作日志。

        Args:
            session: 数据库会话

        Returns:
            删除的数量
        """
        result = await session.exec(select(OperationLog))
        logs = result.all()
        count = len(logs)
        for log in logs:
            await session.delete(log)
        await session.flush()
        return count

    # ============ 系统日志 ============

    async def get_system_logs(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, module: str | None = None, start_time: datetime | None = None, end_time: datetime | None = None) -> tuple[list[SystemLog], int]:
        """获取系统日志列表（支持筛选和分页）。

        Args:
            session: 数据库会话
            page_num: 页码，从1开始
            page_size: 每页数量
            module: 模块名称模糊查询
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            (日志列表, 总数) 元组
        """
        query = select(SystemLog)
        count_query = select(sa_func.count()).select_from(SystemLog)

        # 应用筛选条件
        if module:
            query = query.where(SystemLog.module.contains(module))
            count_query = count_query.where(SystemLog.module.contains(module))
        if start_time:
            query = query.where(SystemLog.request_time >= start_time)
            count_query = count_query.where(SystemLog.request_time >= start_time)
        if end_time:
            query = query.where(SystemLog.request_time <= end_time)
            count_query = count_query.where(SystemLog.request_time <= end_time)

        # 按时间倒序
        query = query.order_by(SystemLog.request_time.desc())

        # 分页
        offset = (page_num - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await session.exec(query)
        logs = list(result.all())

        # 获取总数
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()

        return logs, total

    async def get_system_log_detail(self, session: AsyncSession, log_id: str) -> SystemLog | None:
        """获取系统日志详情。

        Args:
            session: 数据库会话
            log_id: 日志ID

        Returns:
            系统日志对象或 None
        """
        return await self._system_log_crud.get(session, id=log_id, schema_to_select=SystemLog, return_as_model=True)

    async def delete_system_logs(self, session: AsyncSession, log_ids: list[str]) -> int:
        """批量删除系统日志。

        Args:
            session: 数据库会话
            log_ids: 日志ID列表

        Returns:
            删除的数量
        """
        count = 0
        for log_id in log_ids:
            log = await session.get(SystemLog, log_id)
            if log:
                await session.delete(log)
                count += 1
        await session.flush()
        return count

    async def clear_system_logs(self, session: AsyncSession) -> int:
        """清空所有系统日志。

        Args:
            session: 数据库会话

        Returns:
            删除的数量
        """
        result = await session.exec(select(SystemLog))
        logs = result.all()
        count = len(logs)
        for log in logs:
            await session.delete(log)
        await session.flush()
        return count
