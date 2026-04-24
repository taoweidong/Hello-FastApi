"""基础设施层 - 日志端口实现。

将 loguru logger 适配到 LoggingPort 抽象接口。
"""

from src.domain.services.logging_port import LoggingPort
from src.infrastructure.logging.logging_manager import logger


class LoguruLoggingAdapter(LoggingPort):
    """Loguru 日志适配器。

    将 loguru logger 适配到领域层的 LoggingPort 接口。
    """

    def debug(self, message: str, **kwargs: object) -> None:
        logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: object) -> None:
        logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: object) -> None:
        logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: object) -> None:
        logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: object) -> None:
        logger.critical(message, **kwargs)


logging_adapter = LoguruLoggingAdapter()
