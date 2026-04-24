"""字典领域实体。

定义字典的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DictionaryEntity:
    """字典领域实体。

    Attributes:
        id: 字典唯一标识（32位UUID字符串）
        name: 字典名称
        label: 显示标签
        value: 字典值
        sort: 排序号
        is_active: 是否启用
        parent_id: 父字典ID
        description: 描述
        created_time: 创建时间
        updated_time: 更新时间
    """

    id: str
    name: str = ""
    label: str = ""
    value: str = ""
    sort: int = 0
    is_active: int = 1
    parent_id: str | None = None
    description: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None

    # ---- 业务规则方法 ----

    def is_circular_reference(self, parent_id: str | None) -> bool:
        """检查是否会造成循环引用（自身设为自己的子字典）。"""
        return parent_id == self.id

    # ---- 状态变更方法 ----

    def update_info(
        self,
        *,
        name: str | None = None,
        label: str | None = None,
        value: str | None = None,
        sort: int | None = None,
        is_active: int | None = None,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> None:
        """有条件地更新字典信息。"""
        if name is not None:
            self.name = name
        if label is not None:
            self.label = label
        if value is not None:
            self.value = value
        if sort is not None:
            self.sort = sort
        if is_active is not None:
            self.is_active = is_active
        if parent_id is not None:
            self.parent_id = parent_id
        if description is not None:
            self.description = description

    # ---- 工厂方法 ----

    @classmethod
    def create_new(
        cls,
        name: str,
        label: str = "",
        value: str = "",
        sort: int = 0,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> DictionaryEntity:
        """创建新字典实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            name=name,
            label=label,
            value=value,
            sort=sort,
            parent_id=parent_id,
            description=description,
        )
