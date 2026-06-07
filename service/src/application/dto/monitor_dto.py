"""应用层 - 系统监控领域的数据传输对象。"""

from pydantic import BaseModel, field_validator

from src.application.validators import empty_str_to_none


class OnlineLogsQueryDTO(BaseModel):
    """在线用户列表查询请求"""

    username: str | None = None

    @field_validator("username", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)
