"""部门领域实体。

定义部门的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DepartmentEntity:
    """部门领域实体。

    Attributes:
        id: 部门唯一标识（36位UUID字符串）
        name: 部门名称
        parent_id: 父部门ID（可选）
        sort: 排序号
        principal: 负责人（可选）
        phone: 联系电话（可选）
        email: 邮箱（可选）
        status: 状态（0-禁用, 1-启用）
        remark: 备注（可选）
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: str
    name: str
    parent_id: str | None = None
    sort: int = 0
    principal: str | None = None
    phone: str | None = None
    email: str | None = None
    status: int = 1
    remark: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        """是否启用（status=1表示启用）。"""
        return self.status == 1
