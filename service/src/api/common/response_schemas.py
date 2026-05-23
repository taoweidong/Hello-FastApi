"""API 泛型响应 Schema。"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "操作成功"
    data: T | None = None


class PaginationData(BaseModel, Generic[T]):
    items: list[T] = Field(alias="list")
    total: int
    pageSize: int
    currentPage: int


class PaginatedResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "操作成功"
    data: PaginationData[T] | None = None
