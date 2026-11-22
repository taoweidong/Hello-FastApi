"""日志管理路由模块。

提供登录日志、操作日志的查询/批量删除/清空功能，以及系统日志的只读查询功能。
系统日志由中间件自动记录，仅支持查询，不支持手动增删改。
路由直接挂在 /api/system 路径下（无额外前缀）。
"""

from typing import Any

from classy_fastapi import Routable, post
from fastapi import Body, Depends

from src.api.common import list_response, success_response
from src.api.common.response_schemas import ApiResponse, PaginatedResponse
from src.api.dependencies import get_log_service, require_permission
from src.application.dto.log_dto import (
    BatchDeleteLogDTO,
    LoginLogListQueryDTO,
    OperationLogListQueryDTO,
    SystemLogDetailQueryDTO,
    SystemLogListQueryDTO,
)
from src.application.services.log_service import LogService
from src.domain.entities.log import LoginLogEntity, OperationLogEntity


def _format_login_log(log: LoginLogEntity) -> dict[str, Any]:
    """将登录日志实体转为响应字典。"""
    return {
        "id": log.id,
        "status": log.status,
        "ipaddress": log.ipaddress or "",
        "browser": log.browser or "",
        "system": log.system or "",
        "agent": log.agent or "",
        "loginType": log.login_type,
        "creatorId": log.creator_id or "",
        "createdTime": log.created_time.isoformat() if log.created_time else None,
    }


def _format_operation_log(
    log: OperationLogEntity, *, include_payload: bool = False, creator_name: str = ""
) -> dict[str, Any]:
    """将操作/系统日志实体转为响应字典。

    响应瘦身（契约变更）：body / responseResult 属大文本字段，列表行不再随行返回
    （统一置 None），前端需要完整内容时经详情接口 /system-logs-detail 懒加载；
    详情调用方传 include_payload=True 返回全量。

    creatorId 字段语义为"操作人员"展示名：调用方经 LogService.resolve_creator_names
    批量解析出的用户名（字段名保持历史不变，值不再是原始 creator_id UUID）；
    解析不到（用户已删除等）回填空串。
    """
    return {
        "id": log.id,
        "module": log.module or "",
        "path": log.path or "",
        # 大字段：列表行置 None，详情接口返回全量
        "body": (log.body or None) if include_payload else None,
        "method": log.method or "",
        "ipaddress": log.ipaddress or "",
        "browser": log.browser or "",
        "system": log.system or "",
        "responseCode": log.response_code,
        "responseResult": (log.response_result or None) if include_payload else None,
        "statusCode": log.status_code,
        # 操作概要由审计中间件写入（"POST /path - 123ms"），操作日志页「操作概要」列数据源
        "description": log.description or "",
        # 操作人员：批量解析后的用户名（非原始 creator_id），查不到回填空串
        "creatorId": creator_name,
        "createdTime": log.created_time.isoformat() if log.created_time else None,
    }


class LogRouter(Routable):
    """日志管理路由类，提供登录日志、操作日志和系统日志管理功能。"""

    # ============ 登录日志 ============

    @post("/login-logs", response_model=PaginatedResponse[dict])
    async def get_login_logs(
        self,
        query: LoginLogListQueryDTO = Body(default=LoginLogListQueryDTO()),
        service: LogService = Depends(get_log_service),
        _: dict = Depends(require_permission("log:view")),
    ) -> dict:
        """获取登录日志列表。"""
        logs, total = await service.get_login_logs(query)
        log_list = [_format_login_log(log) for log in logs]
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/login-logs/batch-delete", response_model=ApiResponse[dict])
    async def batch_delete_login_logs(
        self,
        dto: BatchDeleteLogDTO,
        service: LogService = Depends(get_log_service),
        _: dict = Depends(require_permission("log:delete")),
    ) -> dict:
        """批量删除登录日志。"""
        count = await service.delete_login_logs(dto)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/login-logs/clear", response_model=ApiResponse[dict])
    async def clear_login_logs(
        self, service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:delete"))
    ) -> dict:
        """清空所有登录日志。"""
        count = await service.clear_login_logs()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")

    # ============ 操作日志（统一日志表 sys_logs） ============

    @post("/operation-logs", response_model=PaginatedResponse[dict])
    async def get_operation_logs(
        self,
        query: OperationLogListQueryDTO = Body(default=OperationLogListQueryDTO()),
        service: LogService = Depends(get_log_service),
        _: dict = Depends(require_permission("log:view")),
    ) -> dict:
        """获取操作日志列表。"""
        logs, total = await service.get_operation_logs(query)
        # 操作人员列：本页 creator_id 收集后一次批量解析（避免逐行查询的 N+1）
        creator_names = await service.resolve_creator_names(logs)
        log_list = [
            _format_operation_log(log, creator_name=creator_names.get(log.creator_id or "", "")) for log in logs
        ]
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/operation-logs/batch-delete", response_model=ApiResponse[dict])
    async def batch_delete_operation_logs(
        self,
        dto: BatchDeleteLogDTO,
        service: LogService = Depends(get_log_service),
        _: dict = Depends(require_permission("log:delete")),
    ) -> dict:
        """批量删除操作日志。"""
        count = await service.delete_operation_logs(dto)
        return success_response(data={"deleted": count}, message=f"已删除 {count} 条记录")

    @post("/operation-logs/clear", response_model=ApiResponse[dict])
    async def clear_operation_logs(
        self, service: LogService = Depends(get_log_service), _: dict = Depends(require_permission("log:delete"))
    ) -> dict:
        """清空所有操作日志。"""
        count = await service.clear_operation_logs()
        return success_response(data={"deleted": count}, message=f"已清空 {count} 条记录")

    # ============ 系统日志（统一日志表 sys_logs，与操作日志共享模型） ============

    @post("/system-logs", response_model=PaginatedResponse[dict])
    async def get_system_logs(
        self,
        query: SystemLogListQueryDTO = Body(default=SystemLogListQueryDTO()),
        service: LogService = Depends(get_log_service),
        _: dict = Depends(require_permission("log:view")),
    ) -> dict:
        """获取系统日志列表。"""
        logs, total = await service.get_system_logs(query)
        # 与操作日志列表同构：操作人员列批量解析用户名（单次 IN 查询）
        creator_names = await service.resolve_creator_names(logs)
        log_list = [
            _format_operation_log(log, creator_name=creator_names.get(log.creator_id or "", "")) for log in logs
        ]
        return list_response(list_data=log_list, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/system-logs-detail", response_model=ApiResponse[dict])
    async def get_system_log_detail(
        self,
        query: SystemLogDetailQueryDTO,
        service: LogService = Depends(get_log_service),
        _: dict = Depends(require_permission("log:view")),
    ) -> dict:
        """获取系统日志详情。"""
        log = await service.get_system_log_detail(query.id)
        if log is None:
            return success_response(data=None, message="日志不存在")
        # 操作人员列与列表同语义：解析 creator_id → 用户名（单条也走批量方法，链路一致）
        creator_names = await service.resolve_creator_names([log])
        creator_name = creator_names.get(log.creator_id or "", "")
        # 详情返回全量（含 body / responseResult 大字段）
        return success_response(data=_format_operation_log(log, include_payload=True, creator_name=creator_name))
