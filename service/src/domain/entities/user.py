"""用户领域实体。

定义用户的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserEntity:
    """用户领域实体。

    Attributes:
        id: 用户唯一标识（36位UUID字符串）
        username: 用户名
        hashed_password: 哈希后的密码
        email: 电子邮箱（可选）
        nickname: 昵称（可选）
        avatar: 头像URL（可选）
        phone: 手机号（可选）
        sex: 性别（0-男, 1-女，可选）
        status: 状态（0-禁用, 1-启用）
        dept_id: 所属部门ID（可选）
        remark: 备注（可选）
        is_superuser: 是否为超级管理员
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: str
    username: str
    hashed_password: str
    email: str | None = None
    nickname: str | None = None
    avatar: str | None = None
    phone: str | None = None
    sex: int | None = None
    status: int = 1
    dept_id: str | None = None
    remark: str | None = None
    is_superuser: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        """是否启用（status=1表示启用）。"""
        return self.status == 1
