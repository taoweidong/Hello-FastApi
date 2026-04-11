"""标准消息响应。"""

from sqlmodel import SQLModel


class MessageResponse(SQLModel):
    """标准消息响应。"""

    message: str
