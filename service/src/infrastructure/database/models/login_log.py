"""登录日志实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.log import LoginLogEntity


class LoginLog(SQLModel, table=True):
    """登录日志实体。"""

    __tablename__ = "sys_login_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    username: str = Field(max_length=50)  # 用户名
    ip: str | None = Field(default=None, max_length=45)  # IP地址
    address: str | None = Field(default=None, max_length=200)  # 登录地点
    system: str | None = Field(default=None, max_length=100)  # 操作系统
    browser: str | None = Field(default=None, max_length=100)  # 浏览器
    status: int = Field(default=1)  # 登录状态(0-失败, 1-成功)
    behavior: str | None = Field(default=None, max_length=200)  # 行为描述
    login_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    def to_domain(self) -> "LoginLogEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.log import LoginLogEntity

        return LoginLogEntity(id=self.id, username=self.username, ip=self.ip, address=self.address, system=self.system, browser=self.browser, status=self.status, behavior=self.behavior, login_time=self.login_time)

    @classmethod
    def from_domain(cls, entity: "LoginLogEntity") -> "LoginLog":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, username=entity.username, ip=entity.ip, address=entity.address, system=entity.system, browser=entity.browser, status=entity.status, behavior=entity.behavior, login_time=entity.login_time)

    def __repr__(self) -> str:
        return f"<LoginLog(id={self.id}, username={self.username})>"
