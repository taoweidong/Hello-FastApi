"""分页响应格式。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """分页响应格式"""

    total: int
    pageNum: int
    pageSize: int
    totalPage: int
    rows: list[T]
