"""日志配置模块。

使用 loguru 实现统一的日志记录，支持：
- 控制台输出（彩色格式）
- 文件输出（按大小轮转）
- 错误日志单独记录
- 访问日志（HTTP 请求）
"""

import sys
from datetime import datetime

from loguru import logger

from src.config.settings import LOGS_DIR, settings

# 移除默认处理器
logger.remove()

# ============ 控制台处理器 ============
logger.add(sys.stdout, level=settings.LOG_LEVEL, format=("<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"), colorize=True, enqueue=True)

# ============ 文件处理器 ============

# 应用程序日志（所有级别）
logger.add(LOGS_DIR / "app.log", level="DEBUG", rotation="10 MB", retention="30 days", compression="zip", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", encoding="utf-8", enqueue=True, filter=lambda record: record["level"].name != "ERROR")

# 错误日志（仅错误级别）
logger.add(LOGS_DIR / "error.log", level="ERROR", rotation="10 MB", retention="60 days", compression="zip", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", encoding="utf-8", enqueue=True, backtrace=True, diagnose=True)

# 访问日志（HTTP 请求）
logger.add(LOGS_DIR / "access.log", level="INFO", rotation="10 MB", retention="30 days", compression="zip", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", encoding="utf-8", enqueue=True, filter=lambda record: record["extra"].get("type") == "access")


def log_request(method: str, path: str, status_code: int, duration_ms: float, client_ip: str) -> None:
    """记录 HTTP 请求日志。

    Args:
        method: HTTP 方法
        path: 请求路径
        status_code: 响应状态码
        duration_ms: 请求处理时间（毫秒）
        client_ip: 客户端 IP 地址
    """
    logger.bind(type="access").info(f"{client_ip} | {method} {path} | {status_code} | {duration_ms:.2f}ms")


def log_startup(app_name: str, version: str) -> None:
    """记录应用启动日志。

    Args:
        app_name: 应用名称
        version: 应用版本
    """
    logger.info(f"{'=' * 60}")
    logger.info(f"启动 {app_name} v{version}")
    logger.info(f"环境: {settings.APP_ENV}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'=' * 60}")


def log_shutdown(app_name: str) -> None:
    """记录应用关闭日志。

    Args:
        app_name: 应用名称
    """
    logger.info(f"{'=' * 60}")
    logger.info(f"关闭 {app_name}")
    logger.info(f"关闭时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'=' * 60}")


__all__ = ["logger", "log_request", "log_startup", "log_shutdown"]
