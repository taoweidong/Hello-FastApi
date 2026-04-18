"""日志领域实体。

定义各类日志的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LoginLogEntity:
    """登录日志领域实体。

    Attributes:
        id: 日志唯一标识（32位UUID字符串）
        status: 登录状态(0-失败, 1-成功)
        ipaddress: IP地址
        browser: 浏览器
        system: 操作系统
        agent: User-Agent信息
        login_type: 登录类型(0-密码, 1-短信, 2-OAuth等)
        creator_id: 创建人ID
        modifier_id: 修改人ID
        created_time: 创建时间
        updated_time: 更新时间
        description: 描述
    """

    id: str
    status: int = 1
    ipaddress: str | None = None
    browser: str | None = None
    system: str | None = None
    agent: str | None = None
    login_type: int = 0
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None

    # ---- 状态查询属性 ----

    @property
    def is_success(self) -> bool:
        """登录是否成功（status=1表示成功）。"""
        return self.status == 1

    # ---- 工厂方法 ----

    @classmethod
    def create_new(cls, status: int = 1, ipaddress: str | None = None, browser: str | None = None, system: str | None = None, agent: str | None = None, login_type: int = 0, description: str | None = None) -> LoginLogEntity:
        """创建新登录日志实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            status=status,
            ipaddress=ipaddress,
            browser=browser,
            system=system,
            agent=agent,
            login_type=login_type,
            description=description,
        )


@dataclass
class OperationLogEntity:
    """统一操作日志领域实体（对应sys_logs表）。

    Attributes:
        id: 日志唯一标识（32位UUID字符串）
        module: 所属模块
        path: 请求路径
        body: 请求体
        method: 请求方法
        ipaddress: IP地址
        browser: 浏览器
        system: 操作系统
        response_code: HTTP响应码
        response_result: 响应结果
        status_code: 业务状态码
        creator_id: 创建人ID
        modifier_id: 修改人ID
        created_time: 创建时间
        updated_time: 更新时间
        description: 描述
    """

    id: str
    module: str | None = None
    path: str | None = None
    body: str | None = None
    method: str | None = None
    ipaddress: str | None = None
    browser: str | None = None
    system: str | None = None
    response_code: int | None = None
    response_result: str | None = None
    status_code: int | None = None
    creator_id: str | None = None
    modifier_id: str | None = None
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None

    # ---- 工厂方法 ----

    @classmethod
    def create_new(
        cls,
        module: str | None = None,
        path: str | None = None,
        method: str | None = None,
        ipaddress: str | None = None,
        browser: str | None = None,
        system: str | None = None,
        response_code: int | None = None,
        response_result: str | None = None,
        status_code: int | None = None,
        description: str | None = None,
    ) -> OperationLogEntity:
        """创建新操作日志实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            module=module,
            path=path,
            method=method,
            ipaddress=ipaddress,
            browser=browser,
            system=system,
            response_code=response_code,
            response_result=response_result,
            status_code=status_code,
            description=description,
        )


# 保留旧名称作为别名，用于向后兼容（后续阶段3会逐步清理）
SystemLogEntity = OperationLogEntity
