"""用户实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, String, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.user import UserEntity


class User(SQLModel, table=True):
    """用户实体。"""

    __tablename__ = "sys_users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    username: str = Field(max_length=50, unique=True, index=True)
    email: str | None = Field(default=None, max_length=100, sa_column_kwargs={"unique": True, "nullable": True}, index=True)
    hashed_password: str = Field(max_length=255)
    nickname: str | None = Field(default=None, max_length=64)  # 昵称
    avatar: str | None = Field(default=None, max_length=500)  # 头像URL
    phone: str | None = Field(default=None, max_length=20)  # 手机号
    sex: int | None = Field(default=None)  # 性别(0-男, 1-女)
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    dept_id: str | None = Field(default=None)  # 部门ID
    remark: str | None = Field(default=None, max_length=500)  # 备注
    is_superuser: bool = Field(default=False)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    # 关系 - 使用字符串引用避免循环导入
    roles: list["UserRole"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})  # noqa: F821

    @property
    def is_active(self) -> bool:
        """是否启用（兼容属性，status=1表示启用）。"""
        return self.status == 1

    def to_domain(self) -> "UserEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.user import UserEntity

        return UserEntity(
            id=self.id,
            username=self.username,
            hashed_password=self.hashed_password,
            email=self.email,
            nickname=self.nickname,
            avatar=self.avatar,
            phone=self.phone,
            sex=self.sex,
            status=self.status,
            dept_id=self.dept_id,
            remark=self.remark,
            is_superuser=self.is_superuser,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "UserEntity") -> "User":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            username=entity.username,
            hashed_password=entity.hashed_password,
            email=entity.email,
            nickname=entity.nickname,
            avatar=entity.avatar,
            phone=entity.phone,
            sex=entity.sex,
            status=entity.status,
            dept_id=entity.dept_id,
            remark=entity.remark,
            is_superuser=entity.is_superuser,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"
