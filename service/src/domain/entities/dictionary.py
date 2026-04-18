"""字典领域实体。

定义字典的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

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
