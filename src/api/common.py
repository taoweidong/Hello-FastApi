"""API 公共组件 - 共享依赖和响应模型。"""

from sqlmodel import SQLModel


class ErrorResponse(SQLModel):
    """标准错误响应。"""

    detail: str


class MessageResponse(SQLModel):
    """标准消息响应。"""

    message: str


class HealthResponse(SQLModel):
    """健康检查响应。"""

    status: str
    version: str
