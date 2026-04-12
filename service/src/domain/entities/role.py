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
