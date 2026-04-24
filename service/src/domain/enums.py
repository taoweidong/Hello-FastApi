"""领域层 - 状态枚举定义。

定义系统通用状态枚举，替代魔法数字。
"""

from __future__ import annotations

from enum import IntEnum


class StatusEnum(IntEnum):
    """通用状态枚举。

    使用 IntEnum 以兼容数据库存储（0/1）和 JSON 序列化。
    """

    INACTIVE = 0
    ACTIVE = 1

    def to_int(self) -> int:
        """转换为整数值，用于数据库存储。"""
        return int(self)

    @classmethod
    def from_int(cls, value: int) -> StatusEnum:
        """从整数值创建枚举。"""
        if value == 0:
            return cls.INACTIVE
        return cls.ACTIVE


class MenuTypeEnum(IntEnum):
    """菜单类型枚举。

    menu_type: 0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限
    """

    DIRECTORY = 0
    MENU = 1
    PERMISSION = 2


class LoginStatusEnum(IntEnum):
    """登录状态枚举。

    status: 0-失败, 1-成功
    """

    FAILED = 0
    SUCCESS = 1
