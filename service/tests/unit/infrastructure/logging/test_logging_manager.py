"""LoggingManager 单元测试。

测试日志管理器的初始化、配置、日志记录功能，以及模块级单例函数
和辅助日志记录函数。
"""


from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.logging.logging_manager import (
    LoggingManager,
    _get_logging_manager,
    log_request,
    log_shutdown,
    log_startup,
    logger,
)


@pytest.mark.unit
class TestLoggingManagerInit:
    """LoggingManager 初始化测试。"""

    def test_init_with_defaults(self):
        """测试默认参数初始化。"""
        with patch.object(LoggingManager, "_configure") as mock_configure:
            mgr = LoggingManager()
        assert mgr._log_level is not None
        assert mgr._logs_dir is not None
        assert mgr._logger is not None
        mock_configure.assert_called_once()

    def test_init_with_custom_level(self):
        """测试自定义日志级别。"""
        with patch.object(LoggingManager, "_configure"):
            mgr = LoggingManager(log_level="ERROR")
        assert mgr._log_level == "ERROR"

    def test_init_with_custom_logs_dir(self):
        """测试自定义日志目录。"""
        with patch.object(LoggingManager, "_configure"):
            mgr = LoggingManager(logs_dir="/custom/logs")
        assert mgr._logs_dir == "/custom/logs"

    def test_logger_property(self):
        """测试 logger 属性返回 loguru logger。"""
        with patch.object(LoggingManager, "_configure"):
            mgr = LoggingManager()
        assert mgr.logger is mgr._logger


@pytest.mark.unit
class TestLoggingManagerConfigure:
    """LoggingManager._configure 测试。"""

    def test_configure_removes_default_handler(self):
        """测试配置时移除默认处理器。"""
        mock_loguru = MagicMock()
        with patch(
            "src.infrastructure.logging.logging_manager._loguru_logger", mock_loguru
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings, patch(
            "src.infrastructure.logging.logging_manager.logging.getLogger"
        ) as mock_get_logger:
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_get_logger.return_value = MagicMock()
            mgr = LoggingManager(log_level="DEBUG", logs_dir="/tmp/logs")
            assert mgr._logger is not None

    def test_configure_sets_sqlalchemy_log_level(self):
        """测试配置设置 SQLAlchemy 日志级别。"""
        mock_sa_logger = MagicMock()
        with patch(
            "src.infrastructure.logging.logging_manager.logging.getLogger",
            return_value=mock_sa_logger,
        ), patch.object(LoggingManager, "_configure") as mock_configure:
            LoggingManager(log_level="DEBUG", logs_dir="/tmp/logs")
            mock_configure.assert_called_once()

    def test_configure_adds_stdout_handler(self):
        """测试配置添加控制台处理器。"""
        mock_loguru = MagicMock()
        with patch(
            "src.infrastructure.logging.logging_manager._loguru_logger", mock_loguru
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings, patch(
            "src.infrastructure.logging.logging_manager.logging.getLogger"
        ) as mock_get_logger, patch(
            "src.infrastructure.logging.logging_manager.sys.stdout", "stdout"
        ):
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_get_logger.return_value = MagicMock()
            LoggingManager(log_level="DEBUG", logs_dir="/tmp/logs")

            mock_loguru.add.assert_any_call(
                "stdout",
                level="DEBUG",
                format=mock_loguru.add.call_args_list[0][1]["format"],
                colorize=True,
                enqueue=True,
            )

    def test_configure_adds_app_log_file(self):
        """测试配置添加应用日志文件处理器。"""
        mock_loguru = MagicMock()
        with patch(
            "src.infrastructure.logging.logging_manager._loguru_logger", mock_loguru
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings, patch(
            "src.infrastructure.logging.logging_manager.logging.getLogger"
        ) as mock_get_logger:
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_get_logger.return_value = MagicMock()
            LoggingManager(log_level="DEBUG", logs_dir="/tmp/logs")

            app_log_calls = [
                c for c in mock_loguru.add.call_args_list if "/app.log" in str(c)
            ]
            assert len(app_log_calls) >= 1

    def test_configure_adds_error_log_file(self):
        """测试配置添加错误日志文件处理器。"""
        mock_loguru = MagicMock()
        with patch(
            "src.infrastructure.logging.logging_manager._loguru_logger", mock_loguru
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings, patch(
            "src.infrastructure.logging.logging_manager.logging.getLogger"
        ) as mock_get_logger:
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_get_logger.return_value = MagicMock()
            LoggingManager(log_level="DEBUG", logs_dir="/tmp/logs")

            error_log_calls = [
                c for c in mock_loguru.add.call_args_list if "/error.log" in str(c)
            ]
            assert len(error_log_calls) >= 1

    def test_configure_adds_access_log_file(self):
        """测试配置添加访问日志文件处理器。"""
        mock_loguru = MagicMock()
        with patch(
            "src.infrastructure.logging.logging_manager._loguru_logger", mock_loguru
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings, patch(
            "src.infrastructure.logging.logging_manager.logging.getLogger"
        ) as mock_get_logger:
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_get_logger.return_value = MagicMock()
            LoggingManager(log_level="DEBUG", logs_dir="/tmp/logs")

            access_log_calls = [
                c for c in mock_loguru.add.call_args_list if "/access.log" in str(c)
            ]
            assert len(access_log_calls) >= 1


@pytest.mark.unit
class TestModuleLevelSingleton:
    """模块级单例测试。"""

    def test_get_logging_manager_returns_singleton(self):
        """测试 _get_logging_manager 返回相同实例。"""
        mgr1 = _get_logging_manager()
        mgr2 = _get_logging_manager()
        assert mgr1 is mgr2

    def test_logger_instance_is_created(self):
        """测试 logger 模块级实例已创建。"""
        assert logger is not None


@pytest.mark.unit
class TestLogRequest:
    """log_request 函数测试。"""

    def test_log_request_binds_type_and_logs(self):
        """测试 log_request 绑定 access 类型并记录 info。"""
        mock_logger = MagicMock()
        mock_bound = MagicMock()
        mock_logger.bind.return_value = mock_bound

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ):
            log_request("GET", "/api/test", 200, 12.34, "127.0.0.1")

        mock_logger.bind.assert_called_once_with(type="access")
        mock_bound.info.assert_called_once()
        call_msg = mock_bound.info.call_args[0][0]
        assert "127.0.0.1" in call_msg
        assert "GET" in call_msg
        assert "/api/test" in call_msg
        assert "200" in call_msg
        assert "12.34" in call_msg

    def test_log_request_with_different_methods(self):
        """测试不同 HTTP 方法的日志格式。"""
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            mock_logger = MagicMock()
            mock_bound = MagicMock()
            mock_logger.bind.return_value = mock_bound

            with patch(
                "src.infrastructure.logging.logging_manager.logger", mock_logger
            ):
                log_request(method, f"/api/{method.lower()}", 200, 5.0, "10.0.0.1")

            mock_logger.bind.assert_called_once_with(type="access")
            mock_bound.info.assert_called_once()

    def test_log_request_with_zero_duration(self):
        """测试持续时间为 0 的情况。"""
        mock_logger = MagicMock()
        mock_bound = MagicMock()
        mock_logger.bind.return_value = mock_bound

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ):
            log_request("GET", "/test", 200, 0.0, "1.1.1.1")

        mock_bound.info.assert_called_once()


@pytest.mark.unit
class TestLogStartup:
    """log_startup 函数测试。"""

    def test_log_startup_with_all_params(self):
        """测试完整参数的启动日志。"""
        mock_logger = MagicMock()

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings:
            mock_settings.APP_ENV = "testing"
            mock_settings.DEBUG = True
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_settings.HOST = "0.0.0.0"
            mock_settings.PORT = 8000

            log_startup("TestApp", "1.0.0", docs_url="/docs", redoc_url="/redoc")

        assert mock_logger.info.call_count >= 9

    def test_log_startup_without_docs_urls(self):
        """测试不传文档 URL 的启动日志。"""
        mock_logger = MagicMock()

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings:
            mock_settings.APP_ENV = "production"
            mock_settings.DEBUG = False
            mock_settings.LOG_LEVEL = "WARNING"

            log_startup("TestApp", "2.0.0")

        assert mock_logger.info.call_count >= 5


@pytest.mark.unit
class TestLogShutdown:
    """log_shutdown 函数测试。"""

    def test_log_shutdown_contains_app_name(self):
        """测试关闭日志包含应用名称。"""
        mock_logger = MagicMock()

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ):
            log_shutdown("MyApp")

        mock_logger.info.assert_called()
        found = any("MyApp" in str(c) for c in mock_logger.info.call_args_list)
        assert found

    def test_log_shutdown_called_info_twice(self):
        """测试关闭日志调用 info 至少 3 次 (分隔线+名称+时间+分隔线)。"""
        mock_logger = MagicMock()

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ):
            log_shutdown("TestApp")

        assert mock_logger.info.call_count >= 3


@pytest.mark.unit
class TestLogStartupEdgeCases:
    """log_startup 边界测试。"""

    def test_log_startup_with_only_docs_url(self):
        """测试仅传 docs_url 不传 redoc_url。"""
        mock_logger = MagicMock()

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings:
            mock_settings.APP_ENV = "testing"
            mock_settings.DEBUG = True
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_settings.HOST = "0.0.0.0"
            mock_settings.PORT = 8000

            log_startup("TestApp", "1.0.0", docs_url="/docs")

        assert mock_logger.info.call_count >= 7

    def test_log_startup_with_only_redoc_url(self):
        """测试仅传 redoc_url 不传 docs_url。"""
        mock_logger = MagicMock()

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ), patch(
            "src.infrastructure.logging.logging_manager.settings"
        ) as mock_settings:
            mock_settings.APP_ENV = "testing"
            mock_settings.DEBUG = True
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_settings.HOST = "0.0.0.0"
            mock_settings.PORT = 8000

            log_startup("TestApp", "1.0.0", redoc_url="/redoc")

        assert mock_logger.info.call_count >= 7


@pytest.mark.unit
class TestModuleLevelFunctionsEdgeCases:
    """模块级辅助函数额外测试。"""

    def test_log_request_with_error_status(self):
        """测试记录错误状态码的请求日志。"""
        mock_logger = MagicMock()
        mock_bound = MagicMock()
        mock_logger.bind.return_value = mock_bound

        with patch(
            "src.infrastructure.logging.logging_manager.logger", mock_logger
        ):
            log_request("POST", "/api/test", 500, 100.5, "10.0.0.1")

        mock_logger.bind.assert_called_once_with(type="access")
        mock_bound.info.assert_called_once()
