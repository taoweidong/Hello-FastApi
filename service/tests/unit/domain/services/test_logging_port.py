"""日志端口接口的单元测试。

测试 LoggingPort 抽象基类的方法签名和返回类型。
"""

import pytest

from src.domain.services.logging_port import LoggingPort


class ConcreteLoggingPort(LoggingPort):
    """用于测试的 LoggingPort 最小化具体实现。"""

    def debug(self, message: str, **kwargs: object) -> None:
        pass

    def info(self, message: str, **kwargs: object) -> None:
        pass

    def warning(self, message: str, **kwargs: object) -> None:
        pass

    def error(self, message: str, **kwargs: object) -> None:
        pass

    def critical(self, message: str, **kwargs: object) -> None:
        pass


@pytest.mark.unit
class TestLoggingPort:
    """LoggingPort 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            LoggingPort()  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        port = ConcreteLoggingPort()
        assert port is not None
        assert isinstance(port, LoggingPort)

    # ---- debug ----

    def test_debug_accepts_str_and_kwargs(self):
        """测试 debug 接受字符串和关键字参数。"""
        port = ConcreteLoggingPort()
        port.debug("debug message")
        port.debug("debug message", extra="data", user_id="123")

    # ---- info ----

    def test_info_accepts_str_and_kwargs(self):
        """测试 info 接受字符串和关键字参数。"""
        port = ConcreteLoggingPort()
        port.info("info message")
        port.info("info message", extra="data", user_id="123")

    # ---- warning ----

    def test_warning_accepts_str_and_kwargs(self):
        """测试 warning 接受字符串和关键字参数。"""
        port = ConcreteLoggingPort()
        port.warning("warning message")
        port.warning("warning message", extra="data", user_id="123")

    # ---- error ----

    def test_error_accepts_str_and_kwargs(self):
        """测试 error 接受字符串和关键字参数。"""
        port = ConcreteLoggingPort()
        port.error("error message")
        port.error("error message", extra="data", user_id="123")

    # ---- critical ----

    def test_critical_accepts_str_and_kwargs(self):
        """测试 critical 接受字符串和关键字参数。"""
        port = ConcreteLoggingPort()
        port.critical("critical message")
        port.critical("critical message", extra="data", user_id="123")
