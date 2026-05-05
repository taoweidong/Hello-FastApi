"""角色领域实体。

定义角色的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RoleEntity:
    """角色领域实体。

    Attributes:
        id: 角色唯一标识（32位UUID字符串）
        name: 角色名称
        code: 角色编码（唯一）
        is_active: 是否启用
        creator_id: 创建人ID
        modifier_id: 修改人ID
        created_time: 创建时间
        updated_time: 更新时间
        description: 角色描述
    """

    id: str
    name: str
    code: str
    is_active: int = 1
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None

    # ---- 状态查询属性 ----

    @property
    def is_active_role(self) -> bool:
        """是否启用。"""
        return self.is_active == 1

    # ---- 状态变更方法 ----

    def activate(self) -> None:
        """启用角色。"""
        self.is_active = 1

    def deactivate(self) -> None:
        """禁用角色。"""
        self.is_active = 0

    def update_info(
        self,
        *,
        name: str | None = None,
        code: str | None = None,
        description: str | None = None,
        is_active: int | None = None,
    ) -> None:
        """有条件地更新角色信息。"""
        if name is not None:
            self.name = name
        if code is not None:
            self.code = code
        if description is not None:
            self.description = description
        if is_active is not None:
            self.is_active = is_active

    # ---- 工厂方法 ----

    @classmethod
    def create_new(cls, name: str, code: str, description: str | None = None) -> RoleEntity:
        """创建新角色实体的工厂方法。"""
        return cls(id=uuid.uuid4().hex, name=name, code=code, description=description, is_active=1)
