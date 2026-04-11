"""标准错误响应。"""

from sqlmodel import SQLModel


class ErrorResponse(SQLModel):
    """标准错误响应。"""

    detail: str
