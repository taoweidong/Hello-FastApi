"""API 公共组件包 - 统一导出所有共享依赖和响应模型。

保持向后兼容：from src.api.common import success_response 仍然可用。
"""

from src.api.common.error_response import ErrorResponse
from src.api.common.health_response import HealthResponse
from src.api.common.message_response import MessageResponse
from src.api.common.model_utils import datetime_to_isoformat, datetime_to_timestamp, model_to_dict, models_to_list, safe_int, safe_str
from src.api.common.page_response import PageResponse
from src.api.common.response_builder import error_response, list_response, page_response, success_response
from src.api.common.unified_response import UnifiedResponse
from src.api.common.user_formatter import format_user_list_row

__all__ = [
    # 响应模型类
    "ErrorResponse",
    "HealthResponse",
    "MessageResponse",
    "PageResponse",
    "UnifiedResponse",
    # 响应构建函数
    "error_response",
    "list_response",
    "page_response",
    "success_response",
    # 用户格式化
    "format_user_list_row",
    # 模型转换工具
    "datetime_to_isoformat",
    "datetime_to_timestamp",
    "model_to_dict",
    "models_to_list",
    "safe_int",
    "safe_str",
]
