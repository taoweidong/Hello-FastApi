"""领域层 - 枚举定义。

定义系统中使用的枚举类型，替代魔法数字。
"""

from enum import IntEnum


class UserStatus(IntEnum):
    """用户状态枚举。"""

    INACTIVE = 0
    ACTIVE = 1


class UserRole(IntEnum):
    """用户角色类型枚举。"""

    USER = 0
    STAFF = 1
    SUPERUSER = 1


class Gender(IntEnum):
    """性别枚举。"""

    UNKNOWN = 0
    MALE = 1
    FEMALE = 2


class PermissionMode(IntEnum):
    """权限模式枚举。"""

    OR = 0  # 满足任一角色即可
    AND = 1  # 必须满足所有角色


class MenuType(IntEnum):
    """菜单类型枚举。"""

    DIRECTORY = 0
    MENU = 1
    PERMISSION = 2


class LoginStatus(IntEnum):
    """登录状态枚举。"""

    FAILED = 0
    SUCCESS = 1
