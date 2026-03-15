"""API 公共组件 - 共享依赖和响应模型。"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """标准错误响应。"""

    detail: str


class MessageResponse(BaseModel):
    """标准消息响应。"""

    message: str


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str
    version: str
