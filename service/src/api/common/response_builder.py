"""响应构建工具函数。"""

from typing import Any, TypeVar

T = TypeVar("T")


def success_response(data: T | None = None, message: str = "操作成功", code: int = 0) -> dict[str, Any]:
    """构建成功响应（Pure Admin 前端标准：code=0 表示成功）"""
    return {"code": code, "message": message, "data": data}


def list_response(list_data: list[T], total: int, page_size: int = 10, current_page: int = 1) -> dict[str, Any]:
    """构建列表响应（Pure Admin 前端标准格式）。

    生成格式: {code: 0, message: "...", data: {list: [...], total: N, pageSize: N, currentPage: N}}
    """
    return success_response(
        data={"list": list_data, "total": total, "pageSize": page_size, "currentPage": current_page}
    )
