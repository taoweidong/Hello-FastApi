"""使用 loguru 的日志配置。"""

import sys
from pathlib import Path

from config.settings import settings
from loguru import logger

# 移除默认处理器
logger.remove()

# 控制台处理器
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    ),
    colorize=True,
)

# 日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 应用程序日志
logger.add(
    log_dir / "app.log",
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# 错误日志
logger.add(
    log_dir / "error.log",
    level="ERROR",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

__all__ = ["logger"]
