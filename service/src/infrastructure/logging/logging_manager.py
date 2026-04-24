"""日志管理器。

使用 loguru 实现统一的日志记录，支持：
- 控制台输出（彩色格式）
- 文件输出（按大小轮转）
- 错误日志单独记录
- 访问日志（HTTP 请求）
"""

import logging
import sys
from datetime import datetime

from loguru import logger as _loguru_logger

from src.config.settings import LOGS_DIR, settings


class LoggingManager:
    """日志管理器，封装 loguru 配置和辅助方法。"""

    def __init__(self, log_level: str | None = None, logs_dir: str | None = None) -> None:
        self._log_level = log_level or settings.LOG_LEVEL
        self._logs_dir = logs_dir or str(LOGS_DIR)
        self._logger = _loguru_logger
        self._configure()

    def _configure(self) -> None:
        """配置 loguru 处理器。"""
        # 禁用 SQLAlchemy 的 INFO 级别日志
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)

        # 移除默认处理器
        self._logger.remove()

        # 控制台处理器
        self._logger.add(
            sys.stdout,
            level=self._log_level,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
            colorize=True,
            enqueue=True,
        )

        # 应用程序日志（所有级别）
        self._logger.add(
            f"{self._logs_dir}/app.log",
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            encoding="utf-8",
            enqueue=True,
            filter=lambda record: record["level"].name != "ERROR",
        )

        # 错误日志（仅错误级别）
        self._logger.add(
            f"{self._logs_dir}/error.log",
            level="ERROR",
            rotation="10 MB",
            retention="60 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True,
        )

        # 访问日志（HTTP 请求）
        self._logger.add(
            f"{self._logs_dir}/access.log",
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            encoding="utf-8",
            enqueue=True,
            filter=lambda record: record["extra"].get("type") == "access",
        )

    @property
    def logger(self):
        """获取 loguru logger 实例。"""
        return self._logger


# ── 模块级单例 & 兼容函数 ──────────────────────────────────────────

_logging_manager: LoggingManager | None = None


def _get_logging_manager() -> LoggingManager:
    """获取或创建 LoggingManager 单例。"""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


# 导出 logger 实例（兼容旧导入：from src.infrastructure.logging.logger import logger）
logger = _get_logging_manager().logger


def log_request(method: str, path: str, status_code: int, duration_ms: float, client_ip: str) -> None:
    """记录 HTTP 请求日志。"""
    logger.bind(type="access").info(f"{client_ip} | {method} {path} | {status_code} | {duration_ms:.2f}ms")


def log_startup(app_name: str, version: str, docs_url: str | None = None, redoc_url: str | None = None) -> None:
    """记录应用启动日志。"""
    logger.info(f"{'=' * 60}")
    logger.info(f"启动 {app_name} v{version}")
    logger.info(f"环境: {settings.APP_ENV}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if docs_url:
        logger.info(f"API 文档 (Swagger): http://{settings.HOST}:{settings.PORT}{docs_url}")
    if redoc_url:
        logger.info(f"API 文档 (ReDoc): http://{settings.HOST}:{settings.PORT}{redoc_url}")
    logger.info(f"{'=' * 60}")


def log_shutdown(app_name: str) -> None:
    """记录应用关闭日志。"""
    logger.info(f"{'=' * 60}")
    logger.info(f"关闭 {app_name}")
    logger.info(f"关闭时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'=' * 60}")


__all__ = ["logger", "log_request", "log_shutdown", "log_startup"]
