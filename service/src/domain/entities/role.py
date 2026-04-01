"""角色领域实体。

定义角色的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RoleEntity:
    """角色领域实体。

    Attributes:
        id: 角色唯一标识（36位UUID字符串）
        name: 角色名称
        code: 角色编码（唯一）
        description: 角色描述（可选）
        status: 状态（0-禁用, 1-启用）
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: str
    name: str
    code: str
    description: str | None = None
    status: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        """是否启用（status=1表示启用）。"""
        return self.status == 1
