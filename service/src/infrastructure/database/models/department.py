"""部门实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.department import DepartmentEntity


class Department(SQLModel, table=True):
    """部门实体（树形结构）。"""

    __tablename__ = "sys_departments"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    mode_type: int = Field(default=0)  # 权限模式(0-OR, 1-AND)
    name: str = Field(max_length=128)  # 部门名称
    code: str = Field(max_length=128, unique=True)  # 部门唯一编码
    rank: int = Field(default=0)  # 排序号
    auto_bind: int = Field(default=0)  # 是否自动绑定角色
    is_active: int = Field(default=1)  # 是否启用
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    parent_id: str | None = Field(default=None, foreign_key="sys_departments.id")  # 父部门ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now()))
    description: str | None = Field(default=None, max_length=256)

    def to_domain(self) -> "DepartmentEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.department import DepartmentEntity

        return DepartmentEntity(
            id=self.id,
            mode_type=self.mode_type,
            name=self.name,
            code=self.code,
            rank=self.rank,
            auto_bind=self.auto_bind,
            is_active=self.is_active,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            parent_id=self.parent_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "DepartmentEntity") -> "Department":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            mode_type=entity.mode_type,
            name=entity.name,
            code=entity.code,
            rank=entity.rank,
            auto_bind=entity.auto_bind,
            is_active=entity.is_active,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            parent_id=entity.parent_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name={self.name})>"
