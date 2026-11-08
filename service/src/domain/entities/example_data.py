"""示例数据领域实体。

Univer 表格 CRUD 示例模块：一张单表数据，前端以电子表格形式增删改查。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class ExampleDataEntity:
    """示例数据实体（单表 CRUD 演示）。

    Attributes:
        id: 主键（32位hex）
        name: 名称（必填）
        category: 类别
        quantity: 数量
        price: 单价
        record_date: 记录日期
        note: 备注
        is_active: 状态（1有效 0停用）
        creator_id / modifier_id / created_time / updated_time: 审计字段
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    category: str | None = None
    quantity: int = 0
    price: float = 0.0
    record_date: date | None = None
    note: str | None = None
    is_active: int = 1
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None

    def update_info(
        self,
        *,
        name: str | None = None,
        category: str | None = None,
        quantity: int | None = None,
        price: float | None = None,
        record_date: date | None = None,
        note: str | None = None,
        is_active: int | None = None,
    ) -> None:
        """有条件地更新字段（None 表示不更新）。"""
        if name is not None:
            self.name = name
        if category is not None:
            self.category = category
        if quantity is not None:
            self.quantity = quantity
        if price is not None:
            self.price = price
        if record_date is not None:
            self.record_date = record_date
        if note is not None:
            self.note = note
        if is_active is not None:
            self.is_active = is_active
