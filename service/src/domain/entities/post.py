"""岗位领域实体。

定义岗位的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PostEntity:
    """岗位领域实体。

    Attributes:
        id: 主键UUID（36位）
        post_code: 岗位编码（唯一）
        post_name: 岗位名称
        post_sort: 显示排序
        is_active: 状态（1正常 0停用）
        remark: 备注
        creator_id: 创建人ID
        modifier_id: 修改人ID
        created_time: 创建时间
        updated_time: 更新时间
    """

    id: str
    post_code: str = ""
    post_name: str = ""
    post_sort: int = 0
    is_active: int = 1
    remark: str = ""
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None

    # ---- 状态变更方法 ----

    def update_info(
        self,
        *,
        post_code: str | None = None,
        post_name: str | None = None,
        post_sort: int | None = None,
        is_active: int | None = None,
        remark: str | None = None,
    ) -> None:
        """有条件地更新岗位信息。"""
        if post_code is not None:
            self.post_code = post_code
        if post_name is not None:
            self.post_name = post_name
        if post_sort is not None:
            self.post_sort = post_sort
        if is_active is not None:
            self.is_active = is_active
        if remark is not None:
            self.remark = remark

    # ---- 工厂方法 ----

    @classmethod
    def create_new(cls, post_code: str, post_name: str, post_sort: int = 0, remark: str = "") -> PostEntity:
        """创建新岗位实体的工厂方法。"""
        return cls(id=str(uuid.uuid4()), post_code=post_code, post_name=post_name, post_sort=post_sort, remark=remark)
