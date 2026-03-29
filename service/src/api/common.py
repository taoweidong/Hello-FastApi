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
    """统一响应格式（Pure Admin 前端标准）"""
    code: int = 0
    message: str = "操作成功"
    data: Any = None


class PageResponse(BaseModel):
    """分页响应格式"""
    total: int
    pageNum: int
    pageSize: int
    totalPage: int
    rows: list


def success_response(data: Any = None, message: str = "操作成功", code: int = 0) -> dict:
    """构建成功响应（Pure Admin 前端标准：code=0 表示成功）"""
    return {"code": code, "message": message, "data": data}


def list_response(list_data: list, total: int, page_size: int = 10, current_page: int = 1) -> dict:
    """构建列表响应（Pure Admin 前端标准格式）
    
    Args:
        list_data: 列表数据
        total: 总记录数
        page_size: 每页大小，默认 10
        current_page: 当前页码，默认 1
    
    Returns:
        符合 Pure Admin 前端标准的分页响应字典
    """
    return success_response(data={
        "list": list_data,
        "total": total,
        "pageSize": page_size,
        "currentPage": current_page
    })


def page_response(rows: list, total: int, page_num: int, page_size: int) -> dict:
    """构建分页响应（旧版，建议使用 list_response）
    
    注意：此函数保留用于向后兼容，新代码请使用 list_response()
    """
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
