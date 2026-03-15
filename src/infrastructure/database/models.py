"""模型注册表 - 导入所有 ORM 模型以确保它们注册到 Base.metadata。

此模块必须在调用 Base.metadata.create_all() 之前导入，
以确保 SQLAlchemy 能够发现所有表。
"""

from src.domain.rbac.entities import Permission, Role, UserRole  # noqa: F401
from src.domain.security.entities import IPRule  # noqa: F401
from src.domain.user.entities import User  # noqa: F401
