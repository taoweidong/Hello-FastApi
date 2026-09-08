"""应用层 - 通知公告领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_to_none


class NoticeCreateDTO(BaseModel):
    """创建通知公告请求"""

    title: str = Field(min_length=1, max_length=128, description="公告标题")
    content: str = Field(default="", description="公告内容")
    noticeType: int = Field(default=1, ge=1, le=2, description="公告类型（1通知 2公告）")
    isActive: int = Field(default=1, ge=0, le=1, description="状态（1正常 0关闭）")


class NoticeUpdateDTO(BaseModel):
    """更新通知公告请求"""

    title: str | None = Field(default=None, min_length=1, max_length=128, description="公告标题")
    content: str | None = Field(default=None, description="公告内容")
    noticeType: int | None = Field(default=None, ge=1, le=2, description="公告类型（1通知 2公告）")
    isActive: int | None = Field(default=None, ge=0, le=1, description="状态（1正常 0关闭）")


class NoticeResponseDTO(BaseModel):
    """通知公告响应"""

    id: str
    title: str
    content: str = ""
    noticeType: int = 1
    isActive: int = 1
    publisherId: str | None = None
    publisherName: str = ""
    creatorId: str | None = None
    modifierId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None

    model_config = {"from_attributes": True}


class NoticeListQueryDTO(BaseModel):
    """通知公告列表查询"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    title: str | None = None
    noticeType: int | None = None
    isActive: int | None = None

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)
