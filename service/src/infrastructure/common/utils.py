"""通用工具函数。"""

import re
from datetime import datetime, timezone


def get_utc_now() -> datetime:
    """获取当前 UTC 时间。"""
    return datetime.now(timezone.utc)


def is_valid_email(email: str) -> bool:
    """验证邮箱格式。"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_strong_password(password: str) -> bool:
    """检查密码是否符合强度要求（最少 8 个字符，1 个大写字母，1 个小写字母，1 个数字）。"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    return bool(re.search(r"\d", password))
