"""系统配置领域实体。

定义系统配置的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemConfigEntity:
    """系统配置领域实体（键值配置）。

    Attributes:
        id: 主键UUID（32位）
        value: 配置值(JSON格式)
        is_active: 是否启用
        access: 访问级别
        key: 配置键(唯一)
        inherit: 是否继承
        creator_id: 创建人ID
        modifier_id: 修改人ID
        created_time: 创建时间
        updated_time: 更新时间
        description: 描述
    """

    id: str
    value: str = ""
    is_active: int = 1
    access: int = 0
    key: str = ""
    inherit: int = 0
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None

    # ---- 状态变更方法 ----

    def update_info(self, *, value: str | None = None, is_active: int | None = None, access: int | None = None, key: str | None = None, inherit: int | None = None, description: str | None = None) -> None:
        """有条件地更新系统配置信息。"""
        if value is not None:
            self.value = value
        if is_active is not None:
            self.is_active = is_active
        if access is not None:
            self.access = access
        if key is not None:
            self.key = key
        if inherit is not None:
            self.inherit = inherit
        if description is not None:
            self.description = description

    # ---- 工厂方法 ----

    @classmethod
    def create_new(cls, key: str, value: str = "", description: str | None = None) -> SystemConfigEntity:
        """创建新系统配置实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            key=key,
            value=value,
            description=description,
        )
