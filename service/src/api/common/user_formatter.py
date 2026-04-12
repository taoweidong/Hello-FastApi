"""用户列表行格式化工具函数。"""

from typing import TypeVar

T = TypeVar("T")


def format_user_list_row(user_dict: dict[str, object]) -> dict[str, object]:
    """将用户 DTO 字典转为 Pure Admin 用户列表行（含 dept、空字符串占位）。"""
    row = dict(user_dict)
    row["dept"] = {"id": row.get("dept_id") or "", "name": ""}
    for key in ("phone", "email", "nickname", "avatar", "description"):
        if row.get(key) is None:
            row[key] = ""
    row.pop("dept_id", None)
    return row
