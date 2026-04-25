"""logger 模块兼容层单元测试。

测试 logger.py 模块重新导出的组件是否与 logging_manager.py 中的
原始组件保持一致。
"""

from src.infrastructure.logging import logging_manager
from src.infrastructure.logging.logger import log_request, log_shutdown, log_startup, logger


class TestLoggerModuleReExports:
    """logger 模块重新导出测试。"""

    def test_logger_is_same_instance(self):
        """测试 logger 实例与 logging_manager.logger 相同。"""
        assert logger is logging_manager.logger

    def test_log_request_is_same_function(self):
        """测试 log_request 函数与 logging_manager.log_request 相同。"""
        assert log_request is logging_manager.log_request

    def test_log_startup_is_same_function(self):
        """测试 log_startup 函数与 logging_manager.log_startup 相同。"""
        assert log_startup is logging_manager.log_startup

    def test_log_shutdown_is_same_function(self):
        """测试 log_shutdown 函数与 logging_manager.log_shutdown 相同。"""
        assert log_shutdown is logging_manager.log_shutdown

    def test_logger_has_standard_methods(self):
        """测试 logger 实例包含标准日志方法。"""
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")
        assert hasattr(logger, "bind")
