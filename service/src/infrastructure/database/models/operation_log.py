"""操作日志实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.log import OperationLogEntity


class OperationLog(SQLModel, table=True):
    """操作日志实体。"""

    __tablename__ = "sys_operation_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    username: str = Field(max_length=50)  # 操作人员
    ip: str | None = Field(default=None, max_length=45)  # IP地址
    address: str | None = Field(default=None, max_length=200)  # 操作地点
    system: str | None = Field(default=None, max_length=100)  # 操作系统
    browser: str | None = Field(default=None, max_length=100)  # 浏览器
    status: int = Field(default=1)  # 操作状态(0-失败, 1-成功)
    summary: str | None = Field(default=None, max_length=200)  # 操作摘要
    module: str | None = Field(default=None, max_length=100)  # 操作模块
    operating_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    def to_domain(self) -> "OperationLogEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.log import OperationLogEntity

        return OperationLogEntity(id=self.id, username=self.username, ip=self.ip, address=self.address, system=self.system, browser=self.browser, status=self.status, summary=self.summary, module=self.module, operating_time=self.operating_time)

    @classmethod
    def from_domain(cls, entity: "OperationLogEntity") -> "OperationLog":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, username=entity.username, ip=entity.ip, address=entity.address, system=entity.system, browser=entity.browser, status=entity.status, summary=entity.summary, module=entity.module, operating_time=entity.operating_time)

    def __repr__(self) -> str:
        return f"<OperationLog(id={self.id}, username={self.username})>"
