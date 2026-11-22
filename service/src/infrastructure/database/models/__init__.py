"""数据库模型包 - 统一导出所有 ORM 模型类。

保持向后兼容：from src.infrastructure.database.models import User 仍然可用。

## 主键生成策略（UUIDv7，RFC 9562）

所有表模型的主键 default_factory 统一使用 ``uuid_utils.compat.uuid7`` 应用侧生成：

- PG18 虽已提供原生 ``uuidv7()``（数据库默认值），但应用侧生成可保持
  SQLite 与 PostgreSQL 双轨行为完全一致（SQLite 无法调用 PG 内置函数）；
- UUIDv7 含 48bit 毫秒时间戳，新数据按时间有序写入，改善主键 B-tree 的
  插入局部性（相比 uuid4 的完全随机散布，减少页分裂与缓存抖动）；
- 存量 uuid4 主键不回填（历史行保持原值），新旧行可共存；
- 32 位 hex 主键用 ``uuid7().hex``、36 位带横线主键用 ``str(uuid7())``，
  列长度（max_length）不变。
"""

from src.infrastructure.database.models.department import Department
from src.infrastructure.database.models.dictionary import Dictionary
from src.infrastructure.database.models.ip_rule import IPRule
from src.infrastructure.database.models.login_log import LoginLog
from src.infrastructure.database.models.menu import Menu
from src.infrastructure.database.models.menu_meta import MenuMeta
from src.infrastructure.database.models.notice import Notice
from src.infrastructure.database.models.post import Post
from src.infrastructure.database.models.role import Role
from src.infrastructure.database.models.role_dept_link import RoleDeptLink
from src.infrastructure.database.models.role_menu_link import RoleMenuLink
from src.infrastructure.database.models.system_config import SystemConfig
from src.infrastructure.database.models.system_log import SystemLog
from src.infrastructure.database.models.user import User
from src.infrastructure.database.models.user_post_link import UserPostLink
from src.infrastructure.database.models.user_role import UserRole

__all__ = [
    "ExampleData",
    "Department",
    "Dictionary",
    "IPRule",
    "LoginLog",
    "Menu",
    "MenuMeta",
    "Notice",
    "Post",
    "Role",
    "RoleDeptLink",
    "RoleMenuLink",
    "SystemConfig",
    "SystemLog",
    "User",
    "UserPostLink",
    "UserRole",
]
from src.infrastructure.database.models.example_data import ExampleData
