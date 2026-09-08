"""通知公告领域实体。

定义通知公告的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NoticeEntity:
    """通知公告领域实体。

    Attributes:
        id: 主键UUID（36位）
        title: 公告标题
        content: 公告内容
        notice_type: 公告类型（1通知 2公告）
        is_active: 状态（1正常 0关闭）
        publisher_id: 发布人ID
        publisher_name: 发布人名称
        creator_id: 创建人ID
        modifier_id: 修改人ID
        created_time: 创建时间
        updated_time: 更新时间
    """

    id: str
    title: str = ""
    content: str = ""
    notice_type: int = 1
    is_active: int = 1
    publisher_id: str | None = None
    publisher_name: str = ""
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None

    # ---- 状态变更方法 ----

    def update_info(
        self,
        *,
        title: str | None = None,
        content: str | None = None,
        notice_type: int | None = None,
        is_active: int | None = None,
    ) -> None:
        """有条件地更新通知公告信息。"""
        if title is not None:
            self.title = title
        if content is not None:
            self.content = content
        if notice_type is not None:
            self.notice_type = notice_type
        if is_active is not None:
            self.is_active = is_active

    # ---- 工厂方法 ----

    @classmethod
    def create_new(
        cls,
        title: str,
        content: str = "",
        notice_type: int = 1,
        publisher_id: str | None = None,
        publisher_name: str = "",
    ) -> NoticeEntity:
        """创建新通知公告实体的工厂方法。"""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            notice_type=notice_type,
            publisher_id=publisher_id,
            publisher_name=publisher_name,
        )
