"""应用层 - 日志领域的数据传输对象。"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ============ 登录日志 DTO ============


class LoginLogListQueryDTO(BaseModel):
    """登录日志列表查询请求"""
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    username: str | None = None
    status: str | None = None  # 前端传递的是字符串 "0" 或 "1"
    loginTime: str | list | None = None  # 前端可能传递空字符串或时间范围数组


class LoginLogResponseDTO(BaseModel):
    """登录日志响应"""
    id: int
    username: str
    ip: str | None = None
    address: str | None = None
    system: str | None = None
    browser: str | None = None
    status: int
    behavior: str | None = None
    loginTime: datetime | None = None

    model_config = {"from_attributes": True}


# ============ 操作日志 DTO ============


class OperationLogListQueryDTO(BaseModel):
    """操作日志列表查询请求"""
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    module: str | None = None
    status: str | None = None
    operatingTime: str | list | None = None  # 前端可能传递空字符串或时间范围数组


class OperationLogResponseDTO(BaseModel):
    """操作日志响应"""
    id: int
    username: str
    ip: str | None = None
    address: str | None = None
    system: str | None = None
    browser: str | None = None
    status: int
    summary: str | None = None
    module: str | None = None
    operatingTime: datetime | None = None

    model_config = {"from_attributes": True}


# ============ 系统日志 DTO ============


class SystemLogListQueryDTO(BaseModel):
    """系统日志列表查询请求"""
    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    module: str | None = None
    requestTime: str | list | None = None  # 前端可能传递空字符串或时间范围数组


class SystemLogResponseDTO(BaseModel):
    """系统日志响应"""
    id: int
    level: str | None = None
    module: str | None = None
    url: str | None = None
    method: str | None = None
    ip: str | None = None
    address: str | None = None
    system: str | None = None
    browser: str | None = None
    takesTime: float | None = None
    requestTime: datetime | None = None

    model_config = {"from_attributes": True}


class SystemLogDetailDTO(BaseModel):
    """系统日志详情响应"""
    id: int
    level: str | None = None
    module: str | None = None
    url: str | None = None
    method: str | None = None
    ip: str | None = None
    address: str | None = None
    system: str | None = None
    browser: str | None = None
    takesTime: float | None = None
    requestTime: datetime | None = None
    requestBody: str | None = None
    responseBody: str | None = None

    model_config = {"from_attributes": True}


# ============ 批量操作 DTO ============


class BatchDeleteLogDTO(BaseModel):
    """批量删除日志请求"""
    ids: list[str]
