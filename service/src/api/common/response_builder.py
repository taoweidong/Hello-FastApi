"""响应构建工具函数。"""

import math
from typing import TypeVar

T = TypeVar("T")


def success_response(data: T | None = None, message: str = "操作成功", code: int = 0) -> dict[str, object]:
    """构建成功响应（Pure Admin 前端标准：code=0 表示成功）

    Returns:
        包含 code, message, data 三个字段的字典
    """
    return {"code": code, "message": message, "data": data}


def list_response(list_data: list[T], total: int, page_size: int = 10, current_page: int = 1) -> dict[str, object]:
    """构建列表响应（Pure Admin 前端标准格式）

    Args:
        list_data: 列表数据
        total: 总记录数
        page_size: 每页大小，默认 10
        current_page: 当前页码，默认 1

    Returns:
        符合 Pure Admin 前端标准的分页响应字典，包含 list, total, pageSize, currentPage
    """
    return success_response(
        data={"list": list_data, "total": total, "pageSize": page_size, "currentPage": current_page}
    )


def page_response(rows: list[T], total: int, page_num: int, page_size: int) -> dict[str, object]:
    """构建分页响应（旧版，建议使用 list_response）

    注意：此函数保留用于向后兼容，新代码请使用 list_response()

    Returns:
        包含 total, pageNum, pageSize, totalPage, rows 的字典
    """
    total_page = math.ceil(total / page_size) if page_size > 0 else 0
    return success_response(
        data={"total": total, "pageNum": page_num, "pageSize": page_size, "totalPage": total_page, "rows": rows}
    )


def error_response(message: str, code: int = 400) -> dict[str, str | int]:
    """构建错误响应

    Returns:
        包含 code, message 两个字段的字典
    """
    return {"code": code, "message": message}
