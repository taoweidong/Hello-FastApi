"""应用层 - 日志服务。

提供日志相关的业务逻辑，包括登录日志和操作日志的查询和管理。
"""

from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.log_dto import BatchDeleteLogDTO, LoginLogListQueryDTO, OperationLogListQueryDTO, SystemLogListQueryDTO
from src.domain.exceptions import NotFoundError
from src.domain.repositories.log_repository import LogRepositoryInterface


def _parse_log_time_bound(value: object) -> datetime | None:
    """解析日志时间边界值。"""
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


class LogService:
    """日志领域操作的应用服务。"""

    def __init__(self, session: AsyncSession, log_repo: LogRepositoryInterface):
        self.session = session
        self.log_repo = log_repo

    # ============ 登录日志 ============

    async def get_login_logs(self, query: LoginLogListQueryDTO) -> tuple[list, int]:
        """获取登录日志列表。"""
        start_time = None
        end_time = None
        if query.createdTime and isinstance(query.createdTime, list) and len(query.createdTime) == 2:
            start_time = _parse_log_time_bound(query.createdTime[0])
            end_time = _parse_log_time_bound(query.createdTime[1])

        status = None
        if query.status:
            status = int(query.status)

        login_type = None
        if query.loginType:
            login_type = int(query.loginType)

        logs, total = await self.log_repo.get_login_logs(
            session=self.session,
            page_num=query.pageNum,
            page_size=query.pageSize,
            status=status,
            start_time=start_time,
            end_time=end_time,
        )
        return logs, total

    async def delete_login_logs(self, dto: BatchDeleteLogDTO) -> int:
        """批量删除登录日志。"""
        count = await self.log_repo.delete_login_logs(session=self.session, log_ids=dto.ids)
        await self.session.flush()
        return count

    async def clear_login_logs(self) -> int:
        """清空所有登录日志。"""
        count = await self.log_repo.clear_login_logs(session=self.session)
        await self.session.flush()
        return count

    # ============ 操作日志（统一日志表 sys_logs） ============

    async def get_operation_logs(self, query: OperationLogListQueryDTO) -> tuple[list, int]:
        """获取操作日志列表。"""
        start_time = None
        end_time = None
        if query.createdTime and isinstance(query.createdTime, list) and len(query.createdTime) == 2:
            start_time = _parse_log_time_bound(query.createdTime[0])
            end_time = _parse_log_time_bound(query.createdTime[1])

        status_code = None
        if query.status:
            status_code = int(query.status)

        logs, total = await self.log_repo.get_operation_logs(
            session=self.session,
            page_num=query.pageNum,
            page_size=query.pageSize,
            module=query.module,
            status_code=status_code,
            start_time=start_time,
            end_time=end_time,
        )
        return logs, total

    async def delete_operation_logs(self, dto: BatchDeleteLogDTO) -> int:
        """批量删除操作日志。"""
        count = await self.log_repo.delete_operation_logs(session=self.session, log_ids=dto.ids)
        await self.session.flush()
        return count

    async def clear_operation_logs(self) -> int:
        """清空所有操作日志。"""
        count = await self.log_repo.clear_operation_logs(session=self.session)
        await self.session.flush()
        return count

    # ============ 系统日志（与操作日志共享 sys_logs 表） ============

    async def get_system_logs(self, query: SystemLogListQueryDTO) -> tuple[list, int]:
        """获取系统日志列表。"""
        start_time = None
        end_time = None
        if query.createdTime and isinstance(query.createdTime, list) and len(query.createdTime) == 2:
            start_time = _parse_log_time_bound(query.createdTime[0])
            end_time = _parse_log_time_bound(query.createdTime[1])

        status_code = None
        if query.status:
            status_code = int(query.status)

        logs, total = await self.log_repo.get_system_logs(
            session=self.session,
            page_num=query.pageNum,
            page_size=query.pageSize,
            module=query.module,
            status_code=status_code,
            start_time=start_time,
            end_time=end_time,
        )
        return logs, total

    async def get_system_log_detail(self, log_id: str):
        """获取系统日志详情。"""
        return await self.log_repo.get_system_log_detail(session=self.session, log_id=log_id)


