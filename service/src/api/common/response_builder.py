"""响应构建工具函数。"""

import math
from typing import Any, TypeVar

T = TypeVar("T")


def success_response(data: T | None = None, message: str = "操作成功", code: int = 0) -> dict[str, Any]:
    """构建成功响应（Pure Admin 前端标准：code=0 表示成功）"""
    return {"code": code, "message": message, "data": data}


def list_response(
    list_data: list[T],
    total: int,
    page_size: int = 10,
    current_page: int = 1,
) -> dict[str, Any]:
    """构建列表响应（Pure Admin 前端标准格式）。

    生成格式: {code: 0, message: "...", data: {list: [...], total: N, pageSize: N, currentPage: N}}
    """
    return success_response(
        data={"list": list_data, "total": total, "pageSize": page_size, "currentPage": current_page}
    )


def page_response(rows: list[T], total: int, page_num: int, page_size: int) -> dict[str, Any]:
    """构建分页响应（旧版，建议使用 list_response）。"""
    total_page = math.ceil(total / page_size) if page_size > 0 else 0
    return success_response(
        data={"total": total, "pageNum": page_num, "pageSize": page_size, "totalPage": total_page, "rows": rows}
    )


def error_response(message: str, code: int = 400) -> dict[str, Any]:
    """构建错误响应"""
    return {"code": code, "message": message}
