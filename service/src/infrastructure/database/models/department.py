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

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=64)  # 部门名称
    parent_id: str | None = Field(default=None, foreign_key="sys_departments.id")  # 父部门ID
    sort: int = Field(default=0)  # 排序号
    principal: str | None = Field(default=None, max_length=50)  # 负责人
    phone: str | None = Field(default=None, max_length=20)  # 联系电话
    email: str | None = Field(default=None, max_length=100)  # 邮箱
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    remark: str | None = Field(default=None, max_length=500)  # 备注
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    def to_domain(self) -> "DepartmentEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.department import DepartmentEntity

        return DepartmentEntity(id=self.id, name=self.name, parent_id=self.parent_id, sort=self.sort, principal=self.principal, phone=self.phone, email=self.email, status=self.status, remark=self.remark, created_at=self.created_at, updated_at=self.updated_at)

    @classmethod
    def from_domain(cls, entity: "DepartmentEntity") -> "Department":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, name=entity.name, parent_id=entity.parent_id, sort=entity.sort, principal=entity.principal, phone=entity.phone, email=entity.email, status=entity.status, remark=entity.remark, created_at=entity.created_at, updated_at=entity.updated_at)

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name={self.name})>"
