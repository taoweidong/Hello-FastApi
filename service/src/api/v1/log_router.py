"""日志管理路由模块。

提供登录日志、操作日志的查询/批量删除/清空功能，以及系统日志的只读查询功能。
系统日志由中间件自动记录，仅支持查询，不支持手动增删改。
路由直接挂在 /api/system 路径下（无额外前缀）。
"""

from classy_fastapi import Routable, post
from fastapi import Body, Depends

from src.api.common import list_response, success_response
from src.api.dependencies import get_log_service, require_permission
from src.application.dto.log_dto import BatchDeleteLogDTO, LoginLogListQueryDTO, OperationLogListQueryDTO, SystemLogListQueryDTO
from src.application.services.log_service import LogService


class LogRouter(Routable):
    """日志管理路由类，提供登录日志、操作日志和系统日志管理功能。"""

    # ============ 登录日志 ============

    @post("/login-logs")
    async def get_login_logs(self, query: LoginLogListQueryDTO = Body(default={}), service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:view"))) -> dict:
        """获取登录日志列表。"""
        logs, total = await service.get_login_logs(query)
        log_list = []
        for log in logs:
            log_list.append(
                {"id": log.id, "status": log.status, "ipaddress": log.ipaddress or "", "browser": log.browser or "", "system": log.system or "", "agent": log.agent or "", "loginType": log.login_type, "creatorId": log.creator_id or "", "createdTime": log.created_time.isoformat() if log.created_time else None}
            )
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/login-logs/batch-delete")
    async def batch_delete_login_logs(self, dto: BatchDeleteLogDTO, service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:delete"))) -> dict:
        """批量删除登录日志。"""
        count = await service.delete_login_logs(dto)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/login-logs/clear")
    async def clear_login_logs(self, service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:delete"))) -> dict:
        """清空所有登录日志。"""
        count = await service.clear_login_logs()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")

    # ============ 操作日志（统一日志表 sys_logs） ============

    @post("/operation-logs")
    async def get_operation_logs(self, query: OperationLogListQueryDTO = Body(default={}), service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:view"))) -> dict:
        """获取操作日志列表。"""
        logs, total = await service.get_operation_logs(query)
        log_list = []
        for log in logs:
            log_list.append(
                {
                    "id": log.id,
                    "module": log.module or "",
                    "path": log.path or "",
                    "body": log.body or "",
                    "method": log.method or "",
                    "ipaddress": log.ipaddress or "",
                    "browser": log.browser or "",
                    "system": log.system or "",
                    "responseCode": log.response_code,
                    "responseResult": log.response_result or "",
                    "statusCode": log.status_code,
                    "creatorId": log.creator_id or "",
                    "createdTime": log.created_time.isoformat() if log.created_time else None,
                }
            )
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/operation-logs/batch-delete")
    async def batch_delete_operation_logs(self, dto: BatchDeleteLogDTO, service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:delete"))) -> dict:
        """批量删除操作日志。"""
        count = await service.delete_operation_logs(dto)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/operation-logs/clear")
    async def clear_operation_logs(self, service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:delete"))) -> dict:
        """清空所有操作日志。"""
        count = await service.clear_operation_logs()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")

    # ============ 系统日志（统一日志表 sys_logs，与操作日志共享模型） ============

    @post("/system-logs")
    async def get_system_logs(self, query: SystemLogListQueryDTO = Body(default={}), service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:view"))) -> dict:
        """获取系统日志列表。"""
        logs, total = await service.get_system_logs(query)
        log_list = []
        for log in logs:
            log_list.append(
                {
                    "id": log.id,
                    "module": log.module or "",
                    "path": log.path or "",
                    "body": log.body or "",
                    "method": log.method or "",
                    "ipaddress": log.ipaddress or "",
                    "browser": log.browser or "",
                    "system": log.system or "",
                    "responseCode": log.response_code,
                    "responseResult": log.response_result or "",
                    "statusCode": log.status_code,
                    "creatorId": log.creator_id or "",
                    "createdTime": log.created_time.isoformat() if log.created_time else None,
                }
            )
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/system-logs-detail")
    async def get_system_log_detail(self, data: dict = Body(default={}), service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:view"))) -> dict:
        """获取系统日志详情。"""
        log_id = data.get("id")
        if not log_id:
            return success_response(data=None, message="缺少日志ID")
        log = await service.get_system_log_detail(log_id)
        if log is None:
            return success_response(data=None, message="日志不存在")
        return success_response(
            data={
                "id": log.id,
                "module": log.module or "",
                "path": log.path or "",
                "body": log.body or "",
                "method": log.method or "",
                "ipaddress": log.ipaddress or "",
                "browser": log.browser or "",
                "system": log.system or "",
                "responseCode": log.response_code,
                "responseResult": log.response_result or "",
                "statusCode": log.status_code,
                "creatorId": log.creator_id or "",
                "createdTime": log.created_time.isoformat() if log.created_time else None,
            }
        )
