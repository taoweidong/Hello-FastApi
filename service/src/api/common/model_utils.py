"""模型转换工具函数。"""

from datetime import datetime

from pydantic import BaseModel
from sqlmodel import SQLModel


def model_to_dict(
    model: BaseModel | SQLModel, exclude_none: bool = False, exclude: set[str] | None = None
) -> dict[str, object]:
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


def models_to_list(
    models: list[BaseModel | SQLModel], exclude_none: bool = False, exclude: set[str] | None = None
) -> list[dict[str, object]]:
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
