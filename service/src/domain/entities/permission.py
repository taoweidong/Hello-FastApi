"""权限领域实体。

定义权限的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PermissionEntity:
    """权限领域实体。

    Attributes:
        id: 权限唯一标识（36位UUID字符串）
        name: 权限名称
        code: 权限编码（唯一）
        category: 权限分类（可选）
        description: 权限描述（可选）
        resource: 资源标识（可选）
        action: 操作类型（可选）
        status: 状态（0-禁用, 1-启用）
        created_at: 创建时间
    """

    id: str
    name: str
    code: str
    category: str | None = None
    description: str | None = None
    resource: str | None = None
    action: str | None = None
    status: int = 1
    created_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        """是否启用（status=1表示启用）。"""
        return self.status == 1
