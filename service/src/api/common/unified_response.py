"""统一响应格式（Pure Admin 前端标准）。"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class UnifiedResponse(BaseModel, Generic[T]):
    """统一响应格式（Pure Admin 前端标准）"""

    code: int = 0
    message: str = "操作成功"
    data: T | None = None
