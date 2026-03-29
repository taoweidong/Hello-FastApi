"""常见验证模式的验证器。"""

import re

from src.core.exceptions import ValidationError


def validate_username(username: str) -> str:
    """验证用户名：3-50个字符，字母数字和下划线。"""
    if not re.match(r"^[a-zA-Z0-9_]{3,50}$", username):
        raise ValidationError("Username must be 3-50 characters, alphanumeric and underscores only")
    return username


def validate_password_strength(password: str) -> str:
    """验证密码强度。"""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit")
    return password
