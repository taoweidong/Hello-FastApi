"""领域与应用层共享的异常类型（不依赖 Web 框架）。"""

from http import HTTPStatus


class AppError(Exception):
    """应用程序基础异常。"""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    """资源未找到。"""

    def __init__(self, detail: str = "资源未找到"):
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=detail)


class ConflictError(AppError):
    """资源已存在或冲突。"""

    def __init__(self, detail: str = "资源已存在"):
        super().__init__(status_code=HTTPStatus.CONFLICT, detail=detail)


class UnauthorizedError(AppError):
    """认证失败。"""

    def __init__(self, detail: str = "需要认证"):
        super().__init__(status_code=HTTPStatus.UNAUTHORIZED, detail=detail)


class ForbiddenError(AppError):
    """权限不足。"""

    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=HTTPStatus.FORBIDDEN, detail=detail)


class ValidationError(AppError):
    """验证错误。"""

    def __init__(self, detail: str = "验证错误"):
        super().__init__(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=detail)


class RateLimitError(AppError):
    """请求频率超限。"""

    def __init__(self, detail: str = "请求过于频繁"):
        super().__init__(status_code=HTTPStatus.TOO_MANY_REQUESTS, detail=detail)


class BusinessError(AppError):
    """业务逻辑错误。"""

    def __init__(self, detail: str = "业务错误"):
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=detail)
