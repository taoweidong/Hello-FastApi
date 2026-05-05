"""部门领域实体。

定义部门的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DepartmentEntity:
    """部门领域实体。

    Attributes:
        id: 部门唯一标识（32位UUID字符串）
        mode_type: 权限模式(0-OR, 1-AND)
        name: 部门名称
        code: 部门唯一编码
        rank: 排序号
        auto_bind: 是否自动绑定角色
        is_active: 是否启用
        creator_id: 创建人ID
        modifier_id: 修改人ID
        parent_id: 父部门ID
        created_time: 创建时间
        updated_time: 更新时间
        description: 描述
    """

    id: str
    mode_type: int = 0
    name: str = ""
    code: str = ""
    rank: int = 0
    auto_bind: int = 0
    is_active: int = 1
    creator_id: str | None = None
    modifier_id: str | None = None
    parent_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None

    # ---- 状态查询属性 ----

    @property
    def is_active_dept(self) -> bool:
        """是否启用。"""
        return self.is_active == 1

    # ---- 业务规则方法 ----

    def is_circular_reference(self, parent_id: str | None) -> bool:
        """检查是否会造成循环引用（自身设为自己的子部门）。"""
        return parent_id == self.id

    # ---- 状态变更方法 ----

    def update_info(
        self,
        *,
        name: str | None = None,
        code: str | None = None,
        mode_type: int | None = None,
        rank: int | None = None,
        auto_bind: int | None = None,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> None:
        """有条件地更新部门信息。"""
        if name is not None:
            self.name = name
        if code is not None:
            self.code = code
        if mode_type is not None:
            self.mode_type = mode_type
        if rank is not None:
            self.rank = rank
        if auto_bind is not None:
            self.auto_bind = auto_bind
        if parent_id is not None:
            self.parent_id = parent_id
        if description is not None:
            self.description = description

    # ---- 工厂方法 ----

    @classmethod
    def create_new(
        cls,
        name: str,
        code: str = "",
        parent_id: str | None = None,
        mode_type: int = 0,
        rank: int = 0,
        auto_bind: int = 0,
        description: str | None = None,
    ) -> DepartmentEntity:
        """创建新部门实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            name=name,
            code=code,
            parent_id=parent_id,
            mode_type=mode_type,
            rank=rank,
            auto_bind=auto_bind,
            description=description,
        )
