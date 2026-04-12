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
