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

    __tablename__ = "sys_userloginlog"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    status: int = Field(default=1)  # 登录状态(0-失败, 1-成功)
    ipaddress: str | None = Field(default=None, max_length=39)  # IP地址
    browser: str | None = Field(default=None, max_length=64)  # 浏览器
    system: str | None = Field(default=None, max_length=64)  # 操作系统
    agent: str | None = Field(default=None, max_length=128)  # User-Agent信息
    login_type: int = Field(default=0)  # 登录类型(0-密码, 1-短信, 2-OAuth等)
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now()))
    description: str | None = Field(default=None, max_length=256)

    def to_domain(self) -> "LoginLogEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.log import LoginLogEntity

        return LoginLogEntity(
            id=self.id, status=self.status, ipaddress=self.ipaddress, browser=self.browser, system=self.system, agent=self.agent, login_type=self.login_type, creator_id=self.creator_id, modifier_id=self.modifier_id, created_time=self.created_time, updated_time=self.updated_time, description=self.description
        )

    @classmethod
    def from_domain(cls, entity: "LoginLogEntity") -> "LoginLog":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            status=entity.status,
            ipaddress=entity.ipaddress,
            browser=entity.browser,
            system=entity.system,
            agent=entity.agent,
            login_type=entity.login_type,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<LoginLog(id={self.id}, status={self.status})>"
