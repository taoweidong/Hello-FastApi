"""API 公共组件 - 共享依赖和响应模型。"""

import math
from typing import Any, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel


class ErrorResponse(SQLModel):
    """标准错误响应。"""

    detail: str


class MessageResponse(SQLModel):
    """标准消息响应。"""

    message: str


class HealthResponse(SQLModel):
    """健康检查响应。"""

    status: str
    version: str


class UnifiedResponse(BaseModel):
    """统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Any = None


class PageResponse(BaseModel):
    """分页响应格式"""
    total: int
    pageNum: int
    pageSize: int
    totalPage: int
    rows: list


def success_response(data: Any = None, message: str = "success", code: int = 200) -> dict:
    """构建成功响应"""
    return {"code": code, "message": message, "data": data}


def page_response(rows: list, total: int, page_num: int, page_size: int) -> dict:
    """构建分页响应"""
    total_page = math.ceil(total / page_size) if page_size > 0 else 0
    return success_response(data={
        "total": total,
        "pageNum": page_num,
        "pageSize": page_size,
        "totalPage": total_page,
        "rows": rows
    })


def error_response(message: str, code: int = 400) -> dict:
    """构建错误响应"""
    return {"code": code, "message": message}
