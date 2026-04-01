"""API 公共组件 - 共享依赖和响应模型。"""

import math
from datetime import datetime
from typing import Any

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
    return success_response(data={"list": list_data, "total": total, "pageSize": page_size, "currentPage": current_page})


def page_response(rows: list, total: int, page_num: int, page_size: int) -> dict:
    """构建分页响应（旧版，建议使用 list_response）

    注意：此函数保留用于向后兼容，新代码请使用 list_response()
    """
    total_page = math.ceil(total / page_size) if page_size > 0 else 0
    return success_response(data={"total": total, "pageNum": page_num, "pageSize": page_size, "totalPage": total_page, "rows": rows})


def error_response(message: str, code: int = 400) -> dict:
    """构建错误响应"""
    return {"code": code, "message": message}


# ============ 模型转换工具 ============


def model_to_dict(model: Any, exclude_none: bool = False, exclude: set[str] | None = None) -> dict:
    """将模型转换为字典。

    Args:
        model: 模型对象（可以是 Pydantic 模型、SQLModel 或普通对象）
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
    # 如果有 __dict__ 属性
    elif hasattr(model, "__dict__"):
        result = {}
        for key, value in model.__dict__.items():
            if not key.startswith("_"):
                if not exclude_none or value is not None:
                    result[key] = value
    else:
        result = {}

    # 排除指定字段
    if exclude:
        result = {k: v for k, v in result.items() if k not in exclude}

    return result


def models_to_list(models: list, exclude_none: bool = False, exclude: set[str] | None = None) -> list[dict]:
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


def safe_str(value: Any, default: str = "") -> str:
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


def safe_int(value: Any, default: int | None = None) -> int | None:
    """安全转换为整数。

    Args:
        value: 待转换的值
        default: 默认值

    Returns:
        转换后的整数，如果转换失败则返回默认值
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
