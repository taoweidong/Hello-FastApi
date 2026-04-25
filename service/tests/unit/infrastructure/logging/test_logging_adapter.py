"""LoguruLoggingAdapter 单元测试。

测试日志适配器是否正确将所有日志级别方法委托给 loguru logger，
以及是否实现了 LoggingPort 抽象方法。
"""

import sys
from abc import ABC

import pytest
from unittest.mock import MagicMock, patch

from src.domain.services.logging_port import LoggingPort
from src.infrastructure.logging.logging_adapter import LoguruLoggingAdapter, logging_adapter

# logging_adapter 在 logging/__init__.py 中通过 from ... import 绑定为实例，
# 直接 import 模块会得到实例而非模块对象，需通过 sys.modules 获取真正的模块。
_logging_adapter_mod = sys.modules["src.infrastructure.logging.logging_adapter"]


@pytest.mark.unit
class TestLoguruLoggingAdapterInit:
    """LoguruLoggingAdapter 初始化与类型测试。"""

    def test_adapter_is_logging_port_subclass(self):
        """测试适配器继承自 LoggingPort。"""
        assert issubclass(LoguruLoggingAdapter, LoggingPort)

    def test_adapter_implements_all_abstract_methods(self):
        """测试适配器实现了 LoggingPort 的所有抽象方法。"""
        abstract_methods = {
            "debug",
            "info",
            "warning",
            "error",
            "critical",
        }
        for method in abstract_methods:
            assert hasattr(LoguruLoggingAdapter, method)

    def test_adapter_not_abstract(self):
        """测试适配器不是抽象类，可以实例化。"""
        try:
            adapter = LoguruLoggingAdapter()
            assert isinstance(adapter, LoguruLoggingAdapter)
        except TypeError:
            pytest.fail("LoguruLoggingAdapter 不应是抽象类")

    def test_module_level_adapter_is_instance(self):
        """测试模块级实例是 LoguruLoggingAdapter。"""
        assert isinstance(logging_adapter, LoguruLoggingAdapter)

    def test_logging_port_is_abc(self):
        """验证 LoggingPort 继承自 ABC。"""
        assert issubclass(LoggingPort, ABC)


@pytest.mark.unit
class TestLoguruLoggingAdapterMethods:
    """LoguruLoggingAdapter 各日志方法测试。"""

    def setup_method(self):
        self.adapter = LoguruLoggingAdapter()

    def test_delegates_debug(self):
        """测试 debug 委托给 logger.debug。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_logger:
            self.adapter.debug("debug message", extra="data")
            mock_logger.debug.assert_called_once_with("debug message", extra="data")

    def test_delegates_info(self):
        """测试 info 委托给 logger.info。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_logger:
            self.adapter.info("info message")
            mock_logger.info.assert_called_once_with("info message")

    def test_delegates_warning(self):
        """测试 warning 委托给 logger.warning。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_logger:
            self.adapter.warning("warning message")
            mock_logger.warning.assert_called_once_with("warning message")

    def test_delegates_error(self):
        """测试 error 委托给 logger.error。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_logger:
            self.adapter.error("error message", exc_info=True)
            mock_logger.error.assert_called_once_with("error message", exc_info=True)

    def test_delegates_critical(self):
        """测试 critical 委托给 logger.critical。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_logger:
            self.adapter.critical("critical message")
            mock_logger.critical.assert_called_once_with("critical message")

    def test_debug_without_kwargs(self):
        """测试 debug 不带额外参数。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_logger:
            self.adapter.debug("plain debug")
            mock_logger.debug.assert_called_once_with("plain debug")

    def test_info_with_multiple_kwargs(self):
        """测试 info 带多个关键字参数。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_logger:
            self.adapter.info("info", user="admin", action="login")
            mock_logger.info.assert_called_once_with("info", user="admin", action="login")

    def test_error_with_no_args(self):
        """测试 error 仅传 message。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_logger:
            self.adapter.error("just error")
            mock_logger.error.assert_called_once_with("just error")

    def test_all_methods_return_none(self):
        """测试所有日志方法返回 None。"""
        with patch.object(_logging_adapter_mod, "logger"):
            assert self.adapter.debug("x") is None
            assert self.adapter.info("x") is None
            assert self.adapter.warning("x") is None
            assert self.adapter.error("x") is None
            assert self.adapter.critical("x") is None

    def test_module_instance_delegates_to_loguru(self):
        """测试模块级实例正确委托给 loguru。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_loguru:
            logging_adapter.info("module adapter test")
            mock_loguru.info.assert_called_once_with("module adapter test")

    def test_warning_with_kwargs(self):
        """测试 warning 带关键字参数。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_loguru:
            self.adapter.warning("warn", user="admin")
            mock_loguru.warning.assert_called_once_with("warn", user="admin")

    def test_critical_with_kwargs(self):
        """测试 critical 带关键字参数。"""
        with patch.object(_logging_adapter_mod, "logger") as mock_loguru:
            self.adapter.critical("critical error", exc_info=True)
            mock_loguru.critical.assert_called_once_with("critical error", exc_info=True)
