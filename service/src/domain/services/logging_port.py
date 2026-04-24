"""领域层 - 日志抽象端口。

定义日志服务的抽象接口，遵循依赖倒置原则。
应用层通过此抽象接口访问日志，不直接依赖基础设施层的具体实现。
"""

from abc import ABC, abstractmethod


class LoggingPort(ABC):
    """日志服务的抽象端口。

    封装日志记录操作，应用层通过此接口记录日志。
    """

    @abstractmethod
    def debug(self, message: str, **kwargs: object) -> None:
        """记录调试级别日志。"""
        ...

    @abstractmethod
    def info(self, message: str, **kwargs: object) -> None:
        """记录信息级别日志。"""
        ...

    @abstractmethod
    def warning(self, message: str, **kwargs: object) -> None:
        """记录警告级别日志。"""
        ...

    @abstractmethod
    def error(self, message: str, **kwargs: object) -> None:
        """记录错误级别日志。"""
        ...

    @abstractmethod
    def critical(self, message: str, **kwargs: object) -> None:
        """记录严重级别日志。"""
        ...
