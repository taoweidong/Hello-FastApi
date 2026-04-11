"""基础设施：日志配置与访问记录。"""

from src.infrastructure.logging.logger import log_request, log_shutdown, log_startup, logger

__all__ = ["logger", "log_request", "log_startup", "log_shutdown"]
