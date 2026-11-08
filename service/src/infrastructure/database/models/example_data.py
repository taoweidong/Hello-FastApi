"""示例数据实体模型（Univer 表格 CRUD 示例）。"""

import uuid
from datetime import date, datetime

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

from src.domain.entities.example_data import ExampleDataEntity


class ExampleData(SQLModel, table=True):
    """示例数据表（sys_example_data）。"""

    __tablename__ = "sys_example_data"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    name: str = Field(max_length=128, index=True)
    category: str | None = Field(default=None, max_length=64)
    quantity: int = Field(default=0)
    price: float = Field(default=0.0)
    record_date: date | None = Field(default=None)
    note: str | None = Field(default=None, max_length=512)
    is_active: int = Field(default=1)
    creator_id: str | None = Field(default=None, max_length=32)
    modifier_id: str | None = Field(default=None, max_length=32)
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now())
    )

    def to_domain(self) -> ExampleDataEntity:
        """将 ORM 模型转换为领域实体。"""
        return ExampleDataEntity(
            id=self.id,
            name=self.name,
            category=self.category,
            quantity=self.quantity,
            price=self.price,
            record_date=self.record_date,
            note=self.note,
            is_active=self.is_active,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
        )

    @classmethod
    def from_domain(cls, entity: ExampleDataEntity) -> "ExampleData":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            name=entity.name,
            category=entity.category,
            quantity=entity.quantity,
            price=entity.price,
            record_date=entity.record_date,
            note=entity.note,
            is_active=entity.is_active,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
        )
