"""日志管理路由模块。

提供登录日志、操作日志、系统日志的查询、批量删除、清空等功能。
路由直接挂在 /api/system 路径下（无额外前缀）。
"""

from fastapi import Body, Depends

from src.api.common import list_response, success_response
from src.api.dependencies import get_current_active_user, get_log_service
from src.application.dto.log_dto import BatchDeleteLogDTO, LoginLogListQueryDTO, OperationLogListQueryDTO, SystemLogListQueryDTO
from src.application.services.log_service import LogService

from classy_fastapi import Routable, post


class LogRouter(Routable):
    """日志管理路由类，提供登录日志、操作日志、系统日志管理功能。"""

    @post("/login-logs")
    async def get_login_logs(
        self,
        query: LoginLogListQueryDTO = Body(default={}),
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """获取登录日志列表。"""
        logs, total = await service.get_login_logs(query)
        log_list = []
        for log in logs:
            log_list.append({"id": log.id, "username": log.username, "ip": log.ip or "", "address": log.address or "", "system": log.system or "", "browser": log.browser or "", "status": log.status, "behavior": log.behavior or "", "loginTime": log.login_time.isoformat() if log.login_time else None})
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/login-logs/batch-delete")
    async def batch_delete_login_logs(
        self,
        dto: BatchDeleteLogDTO,
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """批量删除登录日志。"""
        count = await service.delete_login_logs(dto)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/login-logs/clear")
    async def clear_login_logs(
        self,
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """清空所有登录日志。"""
        count = await service.clear_login_logs()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")

    @post("/operation-logs")
    async def get_operation_logs(
        self,
        query: OperationLogListQueryDTO = Body(default={}),
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """获取操作日志列表。"""
        logs, total = await service.get_operation_logs(query)
        log_list = []
        for log in logs:
            log_list.append(
                {
                    "id": log.id,
                    "username": log.username,
                    "ip": log.ip or "",
                    "address": log.address or "",
                    "system": log.system or "",
                    "browser": log.browser or "",
                    "status": log.status,
                    "summary": log.summary or "",
                    "module": log.module or "",
                    "operatingTime": log.operating_time.isoformat() if log.operating_time else None,
                }
            )
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/operation-logs/batch-delete")
    async def batch_delete_operation_logs(
        self,
        dto: BatchDeleteLogDTO,
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """批量删除操作日志。"""
        count = await service.delete_operation_logs(dto)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/operation-logs/clear")
    async def clear_operation_logs(
        self,
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """清空所有操作日志。"""
        count = await service.clear_operation_logs()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")

    @post("/system-logs")
    async def get_system_logs(
        self,
        query: SystemLogListQueryDTO = Body(default={}),
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """获取系统日志列表。"""
        logs, total = await service.get_system_logs(query)
        log_list = []
        for log in logs:
            log_list.append(
                {
                    "id": log.id,
                    "level": log.level or "",
                    "module": log.module or "",
                    "url": log.url or "",
                    "method": log.method or "",
                    "ip": log.ip or "",
                    "address": log.address or "",
                    "system": log.system or "",
                    "browser": log.browser or "",
                    "takesTime": log.takes_time,
                    "requestTime": log.request_time.isoformat() if log.request_time else None,
                }
            )
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/system-logs-detail")
    async def get_system_logs_detail(
        self,
        data: dict = Body(default={}),
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """获取系统日志详情。"""
        log_id = data.get("id")
        if not log_id:
            return success_response(data=None, message="日志ID不能为空")
        detail = await service.get_system_log_detail(log_id)
        return success_response(data=detail)

    @post("/system-logs/batch-delete")
    async def batch_delete_system_logs(
        self,
        dto: BatchDeleteLogDTO,
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """批量删除系统日志。"""
        count = await service.delete_system_logs(dto)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/system-logs/clear")
    async def clear_system_logs(
        self,
        service: LogService = Depends(get_log_service),
        current_user: dict = Depends(get_current_active_user),
    ) -> dict:
        """清空所有系统日志。"""
        count = await service.clear_system_logs()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")
