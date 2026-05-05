"""批量更新服务层仓储调用 - 移除 session 参数传递。"""

import re
from pathlib import Path


def remove_session_param(file_path: str):
    """移除文件中所有仓储方法调用的 session 参数。"""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    # 替换模式：repo.method(xxx, session) -> repo.method(xxx)
    # repo.method(xxx, self.session) -> repo.method(xxx)
    patterns = [
        (r"(\w+\.get_by_id\([^),]+),\s*(?:self\.)?session\)", r"\1)"),
        (r"(\w+\.get_by_name\([^),]+),\s*(?:self\.)?session\)", r"\1)"),
        (r"(\w+\.get_by_parent_id\([^),]+),\s*(?:self\.)?session\)", r"\1)"),
        (r"(\w+\.create\([^),]+),\s*(?:self\.)?session\)", r"\1)"),
        (r"(\w+\.update\([^),]+),\s*(?:self\.)?session\)", r"\1)"),
        (r"(\w+\.delete\([^),]+),\s*(?:self\.)?session\)", r"\1)"),
        (r"(\w+\.get_all)\((?:self\.)?session\)", r"\1()"),
        (r"(\w+\.get_all)\(session\)", r"\1()"),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    path.write_text(content, encoding="utf-8")
    print(f"✓ 已更新: {file_path}")


if __name__ == "__main__":
    files = ["src/application/services/menu_service.py", "src/application/services/log_service.py", "src/api/v1/auth_routes.py"]

    for f in files:
        try:
            remove_session_param(f)
        except Exception as e:
            print(f"✗ 更新失败 {f}: {e}")
