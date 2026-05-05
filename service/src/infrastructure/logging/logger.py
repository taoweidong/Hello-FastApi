"""日志模块兼容层 - 重新导出 LoggingManager 中的组件。

保持向后兼容：from src.infrastructure.logging.logger import logger 仍然可用。
实际实现在 logging_manager.py 中。
"""

from src.infrastructure.logging.logging_manager import log_request, log_shutdown, log_startup, logger

__all__ = ["logger", "log_request", "log_startup", "log_shutdown"]
