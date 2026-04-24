"""统一操作日志实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Text, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.log import OperationLogEntity


class SystemLog(SQLModel, table=True):
    """统一操作日志实体。"""

    __tablename__ = "sys_logs"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    module: str | None = Field(default=None, max_length=64)  # 所属模块
    path: str | None = Field(default=None, max_length=400)  # 请求路径
    body: str | None = Field(default=None, sa_column=Column(Text, nullable=True))  # 请求体
    method: str | None = Field(default=None, max_length=8)  # 请求方法
    ipaddress: str | None = Field(default=None, max_length=39)  # IP地址
    browser: str | None = Field(default=None, max_length=64)  # 浏览器
    system: str | None = Field(default=None, max_length=64)  # 操作系统
    response_code: int | None = Field(default=None)  # HTTP响应码
    response_result: str | None = Field(default=None, sa_column=Column(Text, nullable=True))  # 响应结果
    status_code: int | None = Field(default=None)  # 业务状态码
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now())
    )
    description: str | None = Field(default=None, max_length=256)

    def to_domain(self) -> "OperationLogEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.log import OperationLogEntity

        return OperationLogEntity(
            id=self.id,
            module=self.module,
            path=self.path,
            body=self.body,
            method=self.method,
            ipaddress=self.ipaddress,
            browser=self.browser,
            system=self.system,
            response_code=self.response_code,
            response_result=self.response_result,
            status_code=self.status_code,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
            created_time=self.created_time,
            updated_time=self.updated_time,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "OperationLogEntity") -> "SystemLog":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            module=entity.module,
            path=entity.path,
            body=entity.body,
            method=entity.method,
            ipaddress=entity.ipaddress,
            browser=entity.browser,
            system=entity.system,
            response_code=entity.response_code,
            response_result=entity.response_result,
            status_code=entity.status_code,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, module={self.module})>"
