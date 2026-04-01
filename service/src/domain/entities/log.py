"""日志领域实体。

定义各类日志的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class LoginLogEntity:
    """登录日志领域实体。

    Attributes:
        id: 日志唯一标识（36位UUID字符串）
        username: 用户名
        ip: IP地址（可选）
        address: 登录地点（可选）
        system: 操作系统（可选）
        browser: 浏览器（可选）
        status: 登录状态（0-失败, 1-成功）
        behavior: 行为描述（可选）
        login_time: 登录时间
    """

    id: str
    username: str
    ip: str | None = None
    address: str | None = None
    system: str | None = None
    browser: str | None = None
    status: int = 1
    behavior: str | None = None
    login_time: datetime | None = None

    @property
    def is_success(self) -> bool:
        """登录是否成功（status=1表示成功）。"""
        return self.status == 1


@dataclass
class OperationLogEntity:
    """操作日志领域实体。

    Attributes:
        id: 日志唯一标识（36位UUID字符串）
        username: 操作人员
        ip: IP地址（可选）
        address: 操作地点（可选）
        system: 操作系统（可选）
        browser: 浏览器（可选）
        status: 操作状态（0-失败, 1-成功）
        summary: 操作摘要（可选）
        module: 操作模块（可选）
        operating_time: 操作时间
    """

    id: str
    username: str
    ip: str | None = None
    address: str | None = None
    system: str | None = None
    browser: str | None = None
    status: int = 1
    summary: str | None = None
    module: str | None = None
    operating_time: datetime | None = None

    @property
    def is_success(self) -> bool:
        """操作是否成功（status=1表示成功）。"""
        return self.status == 1


@dataclass
class SystemLogEntity:
    """系统日志领域实体。

    Attributes:
        id: 日志唯一标识（36位UUID字符串）
        level: 日志级别（可选）
        module: 所属模块（可选）
        url: 请求URL（可选）
        method: 请求方法（可选）
        ip: IP地址（可选）
        address: 请求地点（可选）
        system: 操作系统（可选）
        browser: 浏览器（可选）
        takes_time: 耗时毫秒（可选）
        request_time: 请求时间
        request_body: 请求体（可选）
        response_body: 响应体（可选）
    """

    id: str
    level: str | None = None
    module: str | None = None
    url: str | None = None
    method: str | None = None
    ip: str | None = None
    address: str | None = None
    system: str | None = None
    browser: str | None = None
    takes_time: float | None = None
    request_time: datetime | None = None
    request_body: str | None = None
    response_body: str | None = None
