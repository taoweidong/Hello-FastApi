"""数据库模型定义。

此模块使用 SQLModel 定义所有 ORM 模型。
SQLModel 同时充当 SQLAlchemy ORM 模型和 Pydantic 数据模型，
减少了重复的模型定义代码。
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlmodel import Field, Relationship, SQLModel

# ============ 关联模型 ============


class RolePermissionLink(SQLModel, table=True):
    """角色-权限关联表（用于多对多关系）。"""

    __tablename__ = "role_permissions"

    role_id: str = Field(sa_column=Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True))
    permission_id: str = Field(
        sa_column=Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
    )


# ============ 用户模型 ============


class User(SQLModel, table=True):
    """用户实体。"""

    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=100, unique=True, index=True)
    hashed_password: str = Field(max_length=255)
    full_name: str | None = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )

    # 关系
    roles: list["UserRole"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# ============ RBAC 模型 ============


class Role(SQLModel, table=True):
    """角色实体。"""

    __tablename__ = "roles"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=50, unique=True, index=True)
    description: str | None = Field(default=None, max_length=255)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # 关系
    permissions: list["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermissionLink, sa_relationship_kwargs={"lazy": "selectin"}
    )
    users: list["UserRole"] = Relationship(back_populates="role", sa_relationship_kwargs={"lazy": "selectin"})

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(SQLModel, table=True):
    """权限实体。"""

    __tablename__ = "permissions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=100)
    codename: str = Field(max_length=100, unique=True, index=True)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    resource: str | None = Field(default=None, max_length=50)
    action: str | None = Field(default=None, max_length=20)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # 关系
    roles: list["Role"] = Relationship(
        back_populates="permissions", link_model=RolePermissionLink, sa_relationship_kwargs={"lazy": "selectin"}
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, codename={self.codename})>"


class UserRole(SQLModel, table=True):
    """用户-角色关联表。"""

    __tablename__ = "user_roles"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(sa_column=Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    role_id: str = Field(sa_column=Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False))
    assigned_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )

    # 关系
    user: User | None = Relationship(back_populates="roles")
    role: Role | None = Relationship(back_populates="users")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


# ============ 安全模型 ============


class IPRule(SQLModel, table=True):
    """IP 黑白名单规则实体。"""

    __tablename__ = "ip_rules"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    ip_address: str = Field(max_length=45, index=True)
    rule_type: str = Field(max_length=10)  # "whitelist" 或 "blacklist"
    reason: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    expires_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    def __repr__(self) -> str:
        return f"<IPRule(ip={self.ip_address}, type={self.rule_type})>"
