"""API 公共组件 - 共享依赖和响应模型。"""

import math
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlmodel import SQLModel

# 泛型类型变量
T = TypeVar("T")


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


class UnifiedResponse(BaseModel, Generic[T]):
    """统一响应格式（Pure Admin 前端标准）"""

    code: int = 0
    message: str = "操作成功"
    data: T | None = None


class PageResponse(BaseModel, Generic[T]):
    """分页响应格式"""

    total: int
    pageNum: int
    pageSize: int
    totalPage: int
    rows: list[T]


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
    return success_response(data={"list": list_data, "total": total, "pageSize": page_size, "currentPage": current_page})


def page_response(rows: list[T], total: int, page_num: int, page_size: int) -> dict[str, object]:
    """构建分页响应（旧版，建议使用 list_response）

    注意：此函数保留用于向后兼容，新代码请使用 list_response()

    Returns:
        包含 total, pageNum, pageSize, totalPage, rows 的字典
    """
    total_page = math.ceil(total / page_size) if page_size > 0 else 0
    return success_response(data={"total": total, "pageNum": page_num, "pageSize": page_size, "totalPage": total_page, "rows": rows})


def error_response(message: str, code: int = 400) -> dict[str, str | int]:
    """构建错误响应

    Returns:
        包含 code, message 两个字段的字典
    """
    return {"code": code, "message": message}


def format_user_list_row(user_dict: dict[str, object]) -> dict[str, object]:
    """将用户 DTO 字典转为 Pure Admin 用户列表行（含 dept、空字符串占位）。"""
    row = dict(user_dict)
    row["dept"] = {"id": row.get("dept_id") or "", "name": ""}
    for key in ("phone", "email", "nickname", "avatar", "remark"):
        if row.get(key) is None:
            row[key] = ""
    row.pop("dept_id", None)
    return row


# ============ 模型转换工具 ============


def model_to_dict(model: BaseModel | SQLModel, exclude_none: bool = False, exclude: set[str] | None = None) -> dict[str, object]:
    """将模型转换为字典。

    Args:
        model: 模型对象（Pydantic 模型或 SQLModel）
        exclude_none: 是否排除 None 值
        exclude: 要排除的字段集合

    Returns:
        转换后的字典
    """
    if model is None:
        return {}

    # 如果有 model_dump 方法（Pydantic v2）
    if hasattr(model, "model_dump"):
        result = model.model_dump(exclude_none=exclude_none)
    # 如果有 dict 方法（Pydantic v1）
    elif hasattr(model, "dict"):
        result = model.dict(exclude_none=exclude_none)
    else:
        result = {}

    # 排除指定字段
    if exclude:
        result = {k: v for k, v in result.items() if k not in exclude}

    return result


def models_to_list(models: list[BaseModel | SQLModel], exclude_none: bool = False, exclude: set[str] | None = None) -> list[dict[str, object]]:
    """将模型列表转换为字典列表。

    Args:
        models: 模型列表
        exclude_none: 是否排除 None 值
        exclude: 要排除的字段集合

    Returns:
        转换后的字典列表
    """
    return [model_to_dict(m, exclude_none=exclude_none, exclude=exclude) for m in models]


def datetime_to_isoformat(dt: datetime | None) -> str | None:
    """将 datetime 转换为 ISO 格式字符串。

    Args:
        dt: datetime 对象

    Returns:
        ISO 格式字符串，如果输入为 None 则返回 None
    """
    return dt.isoformat() if dt else None


def datetime_to_timestamp(dt: datetime | None) -> int | None:
    """将 datetime 转换为毫秒时间戳。

    Pure Admin 前端常用毫秒时间戳格式。

    Args:
        dt: datetime 对象

    Returns:
        毫秒时间戳，如果输入为 None 则返回 None
    """
    if dt is None:
        return None
    return int(dt.timestamp() * 1000)


def safe_str(value: object | None, default: str = "") -> str:
    """安全转换为字符串。

    将 None 或空值转换为默认字符串。

    Args:
        value: 待转换的值
        default: 默认值，默认为空字符串

    Returns:
        转换后的字符串
    """
    if value is None or value == "":
        return default
    return str(value)


def safe_int(value: str | int | float | None, default: int | None = None) -> int | None:
    """安全转换为整数。

    Args:
        value: 待转换的值（字符串、整数或浮点数）
        default: 默认值

    Returns:
        转换后的整数，如果转换失败则返回默认值
    """
    if value is None:
        return default
    try:
        if isinstance(value, (str, int, float)):
            return int(value)
        else:
            return default
    except (ValueError, TypeError):
        return default
