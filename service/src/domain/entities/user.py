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
        id: 用户唯一标识（32位UUID字符串）
        password: 哈希后的密码
        last_login: 最后登录时间
        is_superuser: 是否为超级管理员
        username: 用户名
        first_name: 名
        last_name: 姓
        is_staff: 是否为职员
        is_active: 是否启用
        date_joined: 注册时间
        mode_type: 权限模式(0-OR, 1-AND)
        avatar: 头像URL
        nickname: 昵称
        gender: 性别(0-未知, 1-男, 2-女)
        phone: 手机号
        email: 电子邮箱
        creator_id: 创建人ID
        modifier_id: 修改人ID
        dept_id: 所属部门ID
        created_time: 创建时间
        updated_time: 更新时间
        description: 描述
    """

    id: str
    username: str
    password: str
    last_login: datetime | None = None
    is_superuser: int = 0
    first_name: str = ""
    last_name: str = ""
    is_staff: int = 0
    is_active: int = 1
    date_joined: datetime | None = None
    mode_type: int = 0
    avatar: str | None = None
    nickname: str = ""
    gender: int = 0
    phone: str = ""
    email: str = ""
    creator_id: str | None = None
    modifier_id: str | None = None
    dept_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None
