"""健康检查响应。"""

from sqlmodel import SQLModel


class HealthResponse(SQLModel):
    """健康检查响应。"""

    status: str
    version: str
