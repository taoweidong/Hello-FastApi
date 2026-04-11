"""系统日志实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, String, Text, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.log import SystemLogEntity


class SystemLog(SQLModel, table=True):
    """系统日志实体。"""

    __tablename__ = "sys_system_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    level: str | None = Field(default=None, max_length=20)  # 日志级别
    module: str | None = Field(default=None, max_length=100)  # 所属模块
    url: str | None = Field(default=None, max_length=500)  # 请求URL
    method: str | None = Field(default=None, max_length=10)  # 请求方法
    ip: str | None = Field(default=None, max_length=45)  # IP地址
    address: str | None = Field(default=None, max_length=200)  # 请求地点
    system: str | None = Field(default=None, max_length=100)  # 操作系统
    browser: str | None = Field(default=None, max_length=100)  # 浏览器
    takes_time: float | None = Field(default=None)  # 耗时(毫秒)
    request_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    request_body: str | None = Field(default=None, sa_column=Column(Text, nullable=True))  # 请求体
    response_body: str | None = Field(default=None, sa_column=Column(Text, nullable=True))  # 响应体

    def to_domain(self) -> "SystemLogEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.log import SystemLogEntity

        return SystemLogEntity(id=self.id, level=self.level, module=self.module, url=self.url, method=self.method, ip=self.ip, address=self.address, system=self.system, browser=self.browser, takes_time=self.takes_time, request_time=self.request_time, request_body=self.request_body, response_body=self.response_body)

    @classmethod
    def from_domain(cls, entity: "SystemLogEntity") -> "SystemLog":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            level=entity.level,
            module=entity.module,
            url=entity.url,
            method=entity.method,
            ip=entity.ip,
            address=entity.address,
            system=entity.system,
            browser=entity.browser,
            takes_time=entity.takes_time,
            request_time=entity.request_time,
            request_body=entity.request_body,
            response_body=entity.response_body,
        )

    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, module={self.module})>"
