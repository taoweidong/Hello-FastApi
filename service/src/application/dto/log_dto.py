"""应用层 - 日志领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field

from src.application.dto.common import BaseListQueryDTO

# ============ 登录日志 DTO ============


class LoginLogListQueryDTO(BaseListQueryDTO):
    """登录日志列表查询请求"""

    status: str | None = None  # 前端传递的是字符串 "0" 或 "1"
    loginType: str | None = None  # 登录类型
    createdTime: str | list | None = None  # 前端可能传递空字符串或时间范围数组


class LoginLogResponseDTO(BaseModel):
    """登录日志响应"""

    id: str
    status: int = 1
    ipaddress: str | None = None
    browser: str | None = None
    system: str | None = None
    agent: str | None = None
    loginType: int = 0
    creatorId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None

    model_config = {"from_attributes": True}


# ============ 操作日志 DTO ============


class OperationLogListQueryDTO(BaseListQueryDTO):
    """操作日志列表查询请求

    游标语义（keyset 深分页）：beforeTime/beforeId 同时传 signifies
    以上一页最后一行 (created_time, id) 为界取"更旧"的一页（行比较），
    此时 pageNum/offset 被忽略；不传则走传统 offset 分页（完全向后兼容）。
    """

    module: str | None = None
    status: str | None = None
    createdTime: str | list | None = None  # 前端可能传递空字符串或时间范围数组
    beforeTime: str | None = None  # keyset 游标：上一页最后一行的 createdTime（ISO 字符串）
    beforeId: str | None = None  # keyset 游标：上一页最后一行的 id


class OperationLogResponseDTO(BaseModel):
    """操作日志响应。

    body / responseResult 仅在详情接口（/system-logs-detail）返回全量；
    列表接口为响应瘦身置为 None（大字段不随行返回，前端需要时懒加载详情）。
    """

    id: str
    module: str | None = None
    path: str | None = None
    body: str | None = None
    method: str | None = None
    ipaddress: str | None = None
    browser: str | None = None
    system: str | None = None
    responseCode: int | None = None
    responseResult: str | None = None
    statusCode: int | None = None
    creatorId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None

    model_config = {"from_attributes": True}


# ============ 系统日志 DTO ============


class SystemLogListQueryDTO(BaseListQueryDTO):
    """系统日志列表查询请求（游标语义与 OperationLogListQueryDTO 一致）"""

    module: str | None = None
    status: str | None = None
    createdTime: str | list | None = None
    beforeTime: str | None = None  # keyset 游标：上一页最后一行的 createdTime（ISO 字符串）
    beforeId: str | None = None  # keyset 游标：上一页最后一行的 id


# ============ 批量操作 DTO ============


class BatchDeleteLogDTO(BaseModel):
    """批量删除日志请求"""

    ids: list[str]


# ============ 详情查询 DTO ============


class SystemLogDetailQueryDTO(BaseModel):
    """系统日志详情查询请求"""

    id: str = Field(min_length=1)
