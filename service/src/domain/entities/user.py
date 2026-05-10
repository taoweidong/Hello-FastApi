"""用户领域实体。

定义用户的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from src.domain.enums import Gender, PermissionMode, UserRole, UserStatus


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
    is_superuser: UserRole = UserRole.USER
    first_name: str = ""
    last_name: str = ""
    is_staff: UserRole = UserRole.USER
    is_active: UserStatus = UserStatus.ACTIVE
    date_joined: datetime | None = None
    mode_type: PermissionMode = PermissionMode.OR
    avatar: str | None = None
    nickname: str = ""
    gender: Gender = Gender.UNKNOWN
    phone: str = ""
    email: str = ""
    creator_id: str | None = None
    modifier_id: str | None = None
    dept_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None

    # ---- 状态查询属性 ----

    @property
    def is_superuser_user(self) -> bool:
        """是否为超级管理员。"""
        return self.is_superuser == UserRole.SUPERUSER

    @property
    def is_active_user(self) -> bool:
        """是否启用。"""
        return self.is_active == UserStatus.ACTIVE

    # ---- 状态变更方法 ----

    def activate(self) -> None:
        """启用用户。"""
        self.is_active = UserStatus.ACTIVE

    def deactivate(self) -> None:
        """禁用用户。"""
        self.is_active = UserStatus.INACTIVE

    def change_password(self, hashed_password: str) -> None:
        """修改密码（传入已哈希的密码）。"""
        self.password = hashed_password

    def update_profile(
        self,
        *,
        email: str | None = None,
        nickname: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        gender: Gender | None = None,
        avatar: str | None = None,
        is_active: UserStatus | None = None,
        is_staff: UserRole | None = None,
        mode_type: PermissionMode | None = None,
        dept_id: str | None = None,
        description: str | None = None,
    ) -> None:
        """有条件地更新用户档案信息（仅更新非 None 的字段）。"""
        if email is not None:
            self.email = email
        if nickname is not None:
            self.nickname = nickname
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if phone is not None:
            self.phone = phone
        if gender is not None:
            self.gender = gender
        if avatar is not None:
            self.avatar = avatar
        if is_active is not None:
            self.is_active = is_active
        if is_staff is not None:
            self.is_staff = is_staff
        if mode_type is not None:
            self.mode_type = mode_type
        if dept_id is not None:
            self.dept_id = dept_id
        if description is not None:
            self.description = description

    # ---- 工厂方法 ----

    @classmethod
    def create_new(
        cls,
        username: str,
        hashed_password: str,
        email: str = "",
        nickname: str = "",
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
        gender: Gender = Gender.UNKNOWN,
        avatar: str | None = None,
        is_active: UserStatus = UserStatus.ACTIVE,
        is_staff: UserRole = UserRole.USER,
        mode_type: PermissionMode = PermissionMode.OR,
        dept_id: str | None = None,
        description: str | None = None,
    ) -> UserEntity:
        """创建新用户实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            username=username,
            password=hashed_password,
            email=email,
            nickname=nickname,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            gender=gender,
            avatar=avatar,
            is_active=is_active,
            is_staff=is_staff,
            mode_type=mode_type,
            dept_id=dept_id,
            description=description,
        )

    @classmethod
    def create_superuser_entity(
        cls,
        username: str,
        hashed_password: str,
        email: str = "",
        nickname: str = "",
        first_name: str = "",
        last_name: str = "",
        phone: str = "",
        gender: Gender = Gender.UNKNOWN,
        avatar: str | None = None,
        mode_type: PermissionMode = PermissionMode.OR,
        dept_id: str | None = None,
        description: str | None = None,
    ) -> UserEntity:
        """创建超级用户实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            username=username,
            password=hashed_password,
            email=email,
            nickname=nickname,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            gender=gender,
            avatar=avatar,
            is_active=UserStatus.ACTIVE,
            is_staff=UserRole.STAFF,
            is_superuser=UserRole.SUPERUSER,
            mode_type=mode_type,
            dept_id=dept_id,
            description=description,
        )
