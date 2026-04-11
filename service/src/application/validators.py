"""常见验证模式的验证器。"""

import re
from typing import TypeVar

from src.domain.exceptions import ValidationError

T = TypeVar("T")


def validate_username(username: str) -> str:
    """验证用户名：3-50个字符，字母数字和下划线。"""
    if not re.match(r"^[a-zA-Z0-9_]{3,50}$", username):
        raise ValidationError("用户名必须为 3-50 个字符，只允许字母数字和下划线")
    return username


def validate_password_strength(password: str) -> str:
    """验证密码强度。"""
    if len(password) < 8:
        raise ValidationError("密码长度必须至少 8 个字符")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("密码必须包含至少一个大写字母")
    if not re.search(r"[a-z]", password):
        raise ValidationError("密码必须包含至少一个小写字母")
    if not re.search(r"\d", password):
        raise ValidationError("密码必须包含至少一个数字")
    return password


# ============ DTO 通用验证器 ============


def empty_str_to_none(v: str | T) -> str | T | None:
    """将空字符串转换为 None。

    用于 Pydantic field_validator，处理前端传递的空字符串。

    Args:
        v: 待验证的值，可以是字符串或其他类型

    Returns:
        如果输入是空字符串则返回 None，否则返回原值

    Example:
        @field_validator('nickname', mode='before')
        @classmethod
        def validate_nickname(cls, v):
            return empty_str_to_none(v)
    """
    if isinstance(v, str) and v == "":
        return None
    return v


def empty_str_or_zero_to_none(v: int | str | T) -> int | T | None:
    """将空字符串或 0 转换为 None。

    用于 Pydantic field_validator，处理前端传递的空值或零值。
    常用于可选的整型字段（如 dept_id、status 等）。

    Args:
        v: 待验证的值，可以是整型、字符串或其他类型

    Returns:
        如果输入是空字符串、0 或 None 则返回 None，否则返回整数值

    Example:
        @field_validator('dept_id', mode='before')
        @classmethod
        def validate_dept_id(cls, v):
            return empty_str_or_zero_to_none(v)
    """
    if v == "" or v == 0 or v is None:
        return None
    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            return None
    return v


def parse_time_range(time_values: list[str] | None) -> tuple[str | None, str | None]:
    """解析时间范围参数。

    将前端传递的时间范围数组解析为开始时间和结束时间。

    Args:
        time_values: 时间范围数组，包含两个元素 [start_time, end_time]

    Returns:
        元组 (start_time, end_time)，如果输入无效则返回 (None, None)

    Example:
        start_time, end_time = parse_time_range(query.loginTime)
    """
    if time_values and len(time_values) == 2:
        return time_values[0], time_values[1]
    return None, None


def parse_status(status: str | int | None) -> int | None:
    """解析状态参数。

    将前端传递的字符串状态转换为整型。

    Args:
        status: 状态值，可以是字符串或整型

    Returns:
        整型状态值，如果输入无效则返回 None
    """
    if status is None or status == "":
        return None
    if isinstance(status, str):
        try:
            return int(status)
        except ValueError:
            return None
    return status


def normalize_optional_id(v: str | int | None) -> str | None:
    """统一处理可选 ID 字段。

    用于 Pydantic field_validator，处理前端传递的 parentId、deptId 等字段。
    将空字符串、0、'0'、None 统一转换为 None，将整型转换为字符串。

    Args:
        v: 待验证的值，可以是字符串、整型或 None

    Returns:
        统一处理后的字符串 ID，或 None

    Example:
        @field_validator('parentId', 'deptId', mode='before')
        @classmethod
        def validate_id(cls, v):
            return normalize_optional_id(v)
    """
    if v is None or v == "" or v == 0 or v == "0":
        return None
    if isinstance(v, int):
        return str(v)
    return v
