"""用户实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.user import UserEntity


class User(SQLModel, table=True):
    """用户实体。"""

    __tablename__ = "sys_users"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    password: str = Field(max_length=128)  # 密码哈希
    last_login: datetime | None = Field(default=None, sa_column=Column(DateTime(6), nullable=True))  # 最后登录时间
    is_superuser: int = Field(default=0)  # 是否超级用户
    username: str = Field(max_length=150, unique=True, index=True)
    first_name: str = Field(default="", max_length=150)  # 名
    last_name: str = Field(default="", max_length=150)  # 姓
    is_staff: int = Field(default=0)  # 是否为职员
    is_active: int = Field(default=1)  # 是否启用
    date_joined: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))  # 注册时间
    mode_type: int = Field(default=0)  # 权限模式(0-OR, 1-AND)
    avatar: str | None = Field(default=None, max_length=100)  # 头像URL
    nickname: str = Field(default="", max_length=150)  # 昵称
    gender: int = Field(default=0)  # 性别(0-未知, 1-男, 2-女)
    phone: str = Field(default="", max_length=16)  # 手机号
    email: str = Field(default="", max_length=254)  # 邮箱
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    dept_id: str | None = Field(default=None, sa_column=Column(String(32), ForeignKey("sys_departments.id"), nullable=True))  # 部门ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now()))
    description: str | None = Field(default=None, max_length=256)

    # 关系 - 使用字符串引用避免循环导入
    roles: list["UserRole"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})  # noqa: F821

    def to_domain(self) -> "UserEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.user import UserEntity

        return UserEntity(
            id=self.id,
            password=self.password,
            last_login=self.last_login,
            is_superuser=self.is_superuser,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name,
            is_staff=self.is_staff,
            is_active=self.is_active,
            date_joined=self.date_joined,
            mode_type=self.mode_type,
            avatar=self.avatar,
            nickname=self.nickname,
            gender=self.gender,
            phone=self.phone,
            email=self.email,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            dept_id=self.dept_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "UserEntity") -> "User":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            password=entity.password,
            last_login=entity.last_login,
            is_superuser=entity.is_superuser,
            username=entity.username,
            first_name=entity.first_name,
            last_name=entity.last_name,
            is_staff=entity.is_staff,
            is_active=entity.is_active,
            date_joined=entity.date_joined,
            mode_type=entity.mode_type,
            avatar=entity.avatar,
            nickname=entity.nickname,
            gender=entity.gender,
            phone=entity.phone,
            email=entity.email,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            dept_id=entity.dept_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
