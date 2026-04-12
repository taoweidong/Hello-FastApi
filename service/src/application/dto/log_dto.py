"""应用层 - 日志领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field

# ============ 登录日志 DTO ============


class LoginLogListQueryDTO(BaseModel):
    """登录日志列表查询请求"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
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


class OperationLogListQueryDTO(BaseModel):
    """操作日志列表查询请求"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    module: str | None = None
    status: str | None = None
    createdTime: str | list | None = None  # 前端可能传递空字符串或时间范围数组


class OperationLogResponseDTO(BaseModel):
    """操作日志响应"""

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


# ============ 批量操作 DTO ============


class BatchDeleteLogDTO(BaseModel):
    """批量删除日志请求"""

    ids: list[str]
