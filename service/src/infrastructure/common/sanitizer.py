"""敏感信息脱敏工具。

提供敏感信息的脱敏功能，防止密码、令牌等敏感信息泄露到日志中。
"""

import re
from typing import Any

# 敏感字段名称模式
SENSITIVE_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"passwd", re.IGNORECASE),
    re.compile(r"pwd", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"authorization", re.IGNORECASE),
    re.compile(r"apikey", re.IGNORECASE),
    re.compile(r"api_key", re.IGNORECASE),
]


class DataSanitizer:
    """数据脱敏工具类。

    提供对敏感数据的脱敏处理功能。
    """

    @staticmethod
    def sanitize_dict(data: dict[str, Any], mask_char: str = "*") -> dict[str, Any]:
        """脱敏字典中的敏感字段。

        Args:
            data: 原始数据字典
            mask_char: 脱敏字符，默认为 *

        Returns:
            脱敏后的字典
        """
        sanitized = {}
        for key, value in data.items():
            if DataSanitizer._is_sensitive_key(key):
                sanitized[key] = DataSanitizer._mask_value(value, mask_char)
            elif isinstance(value, dict):
                sanitized[key] = DataSanitizer.sanitize_dict(value, mask_char)
            elif isinstance(value, list):
                sanitized[key] = DataSanitizer.sanitize_list(value, mask_char)
            else:
                sanitized[key] = value
        return sanitized

    @staticmethod
    def sanitize_list(data: list[Any], mask_char: str = "*") -> list[Any]:
        """脱敏列表中的敏感字段。

        Args:
            data: 原始数据列表
            mask_char: 脱敏字符，默认为 *

        Returns:
            脱敏后的列表
        """
        sanitized = []
        for item in data:
            if isinstance(item, dict):
                sanitized.append(DataSanitizer.sanitize_dict(item, mask_char))
            elif isinstance(item, list):
                sanitized.append(DataSanitizer.sanitize_list(item, mask_char))
            else:
                sanitized.append(item)
        return sanitized

    @staticmethod
    def sanitize_string(data: str, sensitive_patterns: list[re.Pattern] | None = None) -> str:
        """脱敏字符串中的敏感信息。

        Args:
            data: 原始字符串
            sensitive_patterns: 自定义敏感模式，默认使用内置模式

        Returns:
            脱敏后的字符串
        """
        if sensitive_patterns is None:
            sensitive_patterns = SENSITIVE_PATTERNS

        result = data
        for pattern in sensitive_patterns:
            # 匹配 key: value 格式
            result = re.sub(
                rf'({pattern.pattern})\s*[:=]\s*[\'"]?(\S+)[\'"]?', r"\1: ********", result, flags=re.IGNORECASE
            )
        return result

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        """检查字段名是否为敏感字段。

        Args:
            key: 字段名

        Returns:
            是否为敏感字段
        """
        return any(pattern.search(key) for pattern in SENSITIVE_PATTERNS)

    @staticmethod
    def _mask_value(value: Any, mask_char: str = "*", show_length: bool = False) -> str:
        """对值进行脱敏处理。

        Args:
            value: 原始值
            mask_char: 脱敏字符
            show_length: 是否显示原始长度

        Returns:
            脱敏后的值
        """
        if value is None:
            return None

        value_str = str(value)
        if show_length:
            return f"{mask_char * (len(value_str) - 2)}{value_str[-2:]}"
        return mask_char * min(len(value_str), 8)

    @staticmethod
    def sanitize_exception(exception: Exception) -> str:
        """脱敏异常信息。

        Args:
            exception: 异常对象

        Returns:
            脱敏后的异常信息
        """
        message = str(exception)
        return DataSanitizer.sanitize_string(message)


def safe_log_data(data: Any) -> Any:
    """安全的日志数据转换函数。

    将任意数据转换为可安全记录到日志的格式。

    Args:
        data: 原始数据

    Returns:
        脱敏后的数据
    """
    if isinstance(data, dict):
        return DataSanitizer.sanitize_dict(data)
    elif isinstance(data, list):
        return DataSanitizer.sanitize_list(data)
    elif isinstance(data, str):
        return DataSanitizer.sanitize_string(data)
    elif isinstance(data, Exception):
        return DataSanitizer.sanitize_exception(data)
    else:
        return data
