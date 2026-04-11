"""权限实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, Relationship, SQLModel

# 在模块级别导入关联模型（RolePermissionLink 不依赖 Permission，所以无循环）
from src.infrastructure.database.models.role_permission_link import RolePermissionLink

if TYPE_CHECKING:
    from src.domain.entities.permission import PermissionEntity


class Permission(SQLModel, table=True):
    """权限实体。"""

    __tablename__ = "sys_permissions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=100)
    code: str = Field(max_length=100, unique=True, index=True)  # 权限编码（原codename）
    category: str | None = Field(default=None, max_length=64)  # 权限分类
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    resource: str | None = Field(default=None, max_length=50)
    action: str | None = Field(default=None, max_length=20)
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    # 关系
    roles: list["Role"] = Relationship(back_populates="permissions", link_model=RolePermissionLink, sa_relationship_kwargs={"lazy": "selectin"})  # noqa: F821

    def to_domain(self) -> "PermissionEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.permission import PermissionEntity

        return PermissionEntity(id=self.id, name=self.name, code=self.code, category=self.category, description=self.description, resource=self.resource, action=self.action, status=self.status, created_at=self.created_at)

    @classmethod
    def from_domain(cls, entity: "PermissionEntity") -> "Permission":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, name=entity.name, code=entity.code, category=entity.category, description=entity.description, resource=entity.resource, action=entity.action, status=entity.status, created_at=entity.created_at)

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, code={self.code})>"
