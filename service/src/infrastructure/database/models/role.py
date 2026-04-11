"""角色实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, String, func
from sqlmodel import Field, Relationship, SQLModel

# 在模块级别导入关联模型（RolePermissionLink 不依赖 Role，所以无循环）
from src.infrastructure.database.models.role_permission_link import RolePermissionLink

if TYPE_CHECKING:
    from src.domain.entities.role import RoleEntity


class Role(SQLModel, table=True):
    """角色实体。"""

    __tablename__ = "sys_roles"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=50, unique=True, index=True)
    code: str = Field(max_length=64, sa_column_kwargs={"unique": True})  # 角色编码，唯一
    description: str | None = Field(default=None, max_length=255)
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    # 关系
    permissions: list["Permission"] = Relationship(back_populates="roles", link_model=RolePermissionLink, sa_relationship_kwargs={"lazy": "selectin"})  # noqa: F821
    users: list["UserRole"] = Relationship(back_populates="role", sa_relationship_kwargs={"lazy": "selectin"})  # noqa: F821

    def to_domain(self) -> "RoleEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.role import RoleEntity

        return RoleEntity(id=self.id, name=self.name, code=self.code, description=self.description, status=self.status, created_at=self.created_at, updated_at=self.updated_at)

    @classmethod
    def from_domain(cls, entity: "RoleEntity") -> "Role":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, name=entity.name, code=entity.code, description=entity.description, status=entity.status, created_at=entity.created_at, updated_at=entity.updated_at)

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"
