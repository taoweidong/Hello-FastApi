"""字典实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.dictionary import DictionaryEntity


class Dictionary(SQLModel, table=True):
    """字典实体（树形结构）。"""

    __tablename__ = "sys_dictionary"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    name: str = Field(max_length=128)  # 字典名称
    label: str = Field(default="", max_length=128)  # 显示标签
    value: str = Field(default="", max_length=128)  # 字典值
    sort: int = Field(default=0)  # 排序号
    is_active: int = Field(default=1)  # 是否启用
    parent_id: str | None = Field(default=None, foreign_key="sys_dictionary.id")  # 父字典ID
    description: str | None = Field(default=None, max_length=256)  # 描述
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now()))

    def to_domain(self) -> "DictionaryEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.dictionary import DictionaryEntity

        return DictionaryEntity(id=self.id, name=self.name, label=self.label, value=self.value, sort=self.sort, is_active=self.is_active, parent_id=self.parent_id, description=self.description, created_time=self.created_time, updated_time=self.updated_time)

    @classmethod
    def from_domain(cls, entity: "DictionaryEntity") -> "Dictionary":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, name=entity.name, label=entity.label, value=entity.value, sort=entity.sort, is_active=entity.is_active, parent_id=entity.parent_id, description=entity.description, created_time=entity.created_time, updated_time=entity.updated_time)

    def __repr__(self) -> str:
        return f"<Dictionary(id={self.id}, name={self.name})>"
