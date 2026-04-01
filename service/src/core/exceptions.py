"""应用程序的自定义异常类。"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """应用程序基础异常。"""

    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(AppException):
    """资源未找到。"""

    def __init__(self, detail: str = "资源未找到"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(AppException):
    """资源已存在或冲突。"""

    def __init__(self, detail: str = "资源已存在"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedError(AppException):
    """认证失败。"""

    def __init__(self, detail: str = "需要认证"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(AppException):
    """权限不足。"""

    def __init__(self, detail: str = "权限不足"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(AppException):
    """验证错误。"""

    def __init__(self, detail: str = "验证错误"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class RateLimitError(AppException):
    """请求频率超限。"""

    def __init__(self, detail: str = "请求过于频繁"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


class BusinessError(AppException):
    """业务逻辑错误。"""

    def __init__(self, detail: str = "业务错误"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
