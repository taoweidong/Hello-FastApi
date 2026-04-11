"""应用层 - 日志服务。

提供日志相关的业务逻辑，包括登录日志、操作日志、系统日志的查询和管理。
"""

from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.log_dto import BatchDeleteLogDTO, LoginLogListQueryDTO, OperationLogListQueryDTO, SystemLogListQueryDTO
from src.domain.exceptions import NotFoundError
from src.infrastructure.repositories.log_repository import LogRepository


def _parse_log_time_bound(value: object) -> datetime | None:
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

    def __init__(self, session: AsyncSession, log_repo: LogRepository):
        """初始化日志服务。

        Args:
            session: 数据库会话，用于事务控制
            log_repo: 日志仓储实例
        """
        self.session = session
        self.log_repo = log_repo

    # ============ 登录日志 ============

    async def get_login_logs(self, query: LoginLogListQueryDTO) -> tuple[list, int]:
        """获取登录日志列表。

        Args:
            query: 查询参数

        Returns:
            (日志列表, 总数)
        """
        start_time = None
        end_time = None
        if query.loginTime and len(query.loginTime) == 2:
            start_time = _parse_log_time_bound(query.loginTime[0])
            end_time = _parse_log_time_bound(query.loginTime[1])

        # 处理状态（前端传递的是字符串）
        status = None
        if query.status:
            status = int(query.status)

        logs, total = await self.log_repo.get_login_logs(session=self.session, page_num=query.pageNum, page_size=query.pageSize, username=query.username, status=status, start_time=start_time, end_time=end_time)

        return logs, total

    async def delete_login_logs(self, dto: BatchDeleteLogDTO) -> int:
        """批量删除登录日志。

        Args:
            dto: 删除请求

        Returns:
            删除的数量
        """
        count = await self.log_repo.delete_login_logs(self.session, dto.ids)
        await self.session.commit()
        return count

    async def clear_login_logs(self) -> int:
        """清空所有登录日志。

        Returns:
            删除的数量
        """
        count = await self.log_repo.clear_login_logs(self.session)
        await self.session.commit()
        return count

    # ============ 操作日志 ============

    async def get_operation_logs(self, query: OperationLogListQueryDTO) -> tuple[list, int]:
        """获取操作日志列表。

        Args:
            query: 查询参数

        Returns:
            (日志列表, 总数)
        """
        start_time = None
        end_time = None
        if query.operatingTime and len(query.operatingTime) == 2:
            start_time = _parse_log_time_bound(query.operatingTime[0])
            end_time = _parse_log_time_bound(query.operatingTime[1])

        # 处理状态
        status = None
        if query.status:
            status = int(query.status)

        logs, total = await self.log_repo.get_operation_logs(session=self.session, page_num=query.pageNum, page_size=query.pageSize, module=query.module, status=status, start_time=start_time, end_time=end_time)

        return logs, total

    async def delete_operation_logs(self, dto: BatchDeleteLogDTO) -> int:
        """批量删除操作日志。

        Args:
            dto: 删除请求

        Returns:
            删除的数量
        """
        count = await self.log_repo.delete_operation_logs(self.session, dto.ids)
        await self.session.commit()
        return count

    async def clear_operation_logs(self) -> int:
        """清空所有操作日志。

        Returns:
            删除的数量
        """
        count = await self.log_repo.clear_operation_logs(self.session)
        await self.session.commit()
        return count

    # ============ 系统日志 ============

    async def get_system_logs(self, query: SystemLogListQueryDTO) -> tuple[list, int]:
        """获取系统日志列表。

        Args:
            query: 查询参数

        Returns:
            (日志列表, 总数)
        """
        start_time = None
        end_time = None
        if query.requestTime and len(query.requestTime) == 2:
            start_time = _parse_log_time_bound(query.requestTime[0])
            end_time = _parse_log_time_bound(query.requestTime[1])

        logs, total = await self.log_repo.get_system_logs(session=self.session, page_num=query.pageNum, page_size=query.pageSize, module=query.module, start_time=start_time, end_time=end_time)

        return logs, total

    async def get_system_log_detail(self, log_id: str) -> dict:
        """获取系统日志详情。

        Args:
            log_id: 日志ID

        Returns:
            日志详情

        Raises:
            NotFoundError: 日志不存在
        """
        log = await self.log_repo.get_system_log_detail(self.session, log_id)
        if not log:
            raise NotFoundError("日志不存在")

        return {
            "id": log.id,
            "level": log.level,
            "module": log.module,
            "url": log.url,
            "method": log.method,
            "ip": log.ip,
            "address": log.address,
            "system": log.system,
            "browser": log.browser,
            "takesTime": log.takes_time,
            "requestTime": log.request_time,
            "requestBody": log.request_body,
            "responseBody": log.response_body,
        }

    async def delete_system_logs(self, dto: BatchDeleteLogDTO) -> int:
        """批量删除系统日志。

        Args:
            dto: 删除请求

        Returns:
            删除的数量
        """
        count = await self.log_repo.delete_system_logs(self.session, dto.ids)
        await self.session.commit()
        return count

    async def clear_system_logs(self) -> int:
        """清空所有系统日志。

        Returns:
            删除的数量
        """
        count = await self.log_repo.clear_system_logs(self.session)
        await self.session.commit()
        return count
