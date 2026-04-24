"""角色实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.role import RoleEntity


class Role(SQLModel, table=True):
    """角色实体。"""

    __tablename__ = "sys_roles"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    name: str = Field(max_length=128, unique=True, index=True)
    code: str = Field(max_length=128, sa_column_kwargs={"unique": True})  # 角色编码，唯一
    is_active: int = Field(default=1)  # 是否启用
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now())
    )
    description: str | None = Field(default=None, max_length=256)

    # 关系 - 使用字符串引用避免循环导入
    users: list["UserRole"] = Relationship(back_populates="role", sa_relationship_kwargs={"lazy": "selectin"})  # noqa: F821

    def to_domain(self) -> "RoleEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.role import RoleEntity

        return RoleEntity(
            id=self.id,
            name=self.name,
            code=self.code,
            is_active=self.is_active,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "RoleEntity") -> "Role":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            name=entity.name,
            code=entity.code,
            is_active=entity.is_active,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"
