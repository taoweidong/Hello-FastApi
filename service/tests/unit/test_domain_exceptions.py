"""领域异常的单元测试。

测试 src.domain.exceptions 中的所有异常类型。
"""

from http import HTTPStatus

import pytest

from src.domain.exceptions import (
    AppError,
    BusinessError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)


@pytest.mark.unit
class TestAppError:
    """AppError 基础异常测试。"""

    def test_init(self):
        """测试基础异常初始化。"""
        err = AppError(status_code=400, detail="自定义错误")
        assert err.status_code == 400
        assert err.detail == "自定义错误"
        assert str(err) == "自定义错误"

    def test_is_exception(self):
        """测试异常继承。"""
        err = AppError(status_code=400, detail="test")
        assert isinstance(err, Exception)

    def test_custom_status_code(self):
        """测试自定义状态码。"""
        err = AppError(status_code=418, detail="I'm a teapot")
        assert err.status_code == 418


@pytest.mark.unit
class TestNotFoundError:
    """NotFoundError 测试。"""

    def test_default_detail(self):
        """测试默认错误消息。"""
        err = NotFoundError()
        assert err.detail == "资源未找到"
        assert err.status_code == HTTPStatus.NOT_FOUND

    def test_custom_detail(self):
        """测试自定义错误消息。"""
        err = NotFoundError("用户不存在")
        assert err.detail == "用户不存在"

    def test_inherits_app_error(self):
        """测试继承关系。"""
        assert issubclass(NotFoundError, AppError)


@pytest.mark.unit
class TestConflictError:
    """ConflictError 测试。"""

    def test_default_detail(self):
        """测试默认错误消息。"""
        err = ConflictError()
        assert err.detail == "资源已存在"
        assert err.status_code == HTTPStatus.CONFLICT

    def test_custom_detail(self):
        """测试自定义错误消息。"""
        err = ConflictError("用户名已重复")
        assert err.detail == "用户名已重复"

    def test_inherits_app_error(self):
        """测试继承关系。"""
        assert issubclass(ConflictError, AppError)


@pytest.mark.unit
class TestUnauthorizedError:
    """UnauthorizedError 测试。"""

    def test_default_detail(self):
        """测试默认错误消息。"""
        err = UnauthorizedError()
        assert err.detail == "需要认证"
        assert err.status_code == HTTPStatus.UNAUTHORIZED

    def test_custom_detail(self):
        """测试自定义错误消息。"""
        err = UnauthorizedError("令牌无效")
        assert err.detail == "令牌无效"

    def test_inherits_app_error(self):
        """测试继承关系。"""
        assert issubclass(UnauthorizedError, AppError)


@pytest.mark.unit
class TestForbiddenError:
    """ForbiddenError 测试。"""

    def test_default_detail(self):
        """测试默认错误消息。"""
        err = ForbiddenError()
        assert err.detail == "权限不足"
        assert err.status_code == HTTPStatus.FORBIDDEN

    def test_custom_detail(self):
        """测试自定义错误消息。"""
        err = ForbiddenError("无管理员权限")
        assert err.detail == "无管理员权限"

    def test_inherits_app_error(self):
        """测试继承关系。"""
        assert issubclass(ForbiddenError, AppError)


@pytest.mark.unit
class TestValidationError:
    """ValidationError 测试。"""

    def test_default_detail(self):
        """测试默认错误消息。"""
        err = ValidationError()
        assert err.detail == "验证错误"
        assert err.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_custom_detail(self):
        """测试自定义错误消息。"""
        err = ValidationError("字段格式错误")
        assert err.detail == "字段格式错误"

    def test_inherits_app_error(self):
        """测试继承关系。"""
        assert issubclass(ValidationError, AppError)


@pytest.mark.unit
class TestRateLimitError:
    """RateLimitError 测试。"""

    def test_default_detail(self):
        """测试默认错误消息。"""
        err = RateLimitError()
        assert err.detail == "请求过于频繁"
        assert err.status_code == HTTPStatus.TOO_MANY_REQUESTS

    def test_custom_detail(self):
        """测试自定义错误消息。"""
        err = RateLimitError("请稍后再试")
        assert err.detail == "请稍后再试"

    def test_inherits_app_error(self):
        """测试继承关系。"""
        assert issubclass(RateLimitError, AppError)


@pytest.mark.unit
class TestBusinessError:
    """BusinessError 测试。"""

    def test_default_detail(self):
        """测试默认错误消息。"""
        err = BusinessError()
        assert err.detail == "业务错误"
        assert err.status_code == HTTPStatus.BAD_REQUEST

    def test_custom_detail(self):
        """测试自定义错误消息。"""
        err = BusinessError("父部门不存在")
        assert err.detail == "父部门不存在"

    def test_inherits_app_error(self):
        """测试继承关系。"""
        assert issubclass(BusinessError, AppError)


@pytest.mark.unit
class TestExceptionInheritance:
    """测试异常继承层次。"""

    def test_all_domain_errors_inherit_from_app_error(self):
        """测试所有领域异常都继承自 AppError。"""
        error_classes = [
            NotFoundError,
            ConflictError,
            UnauthorizedError,
            ForbiddenError,
            ValidationError,
            RateLimitError,
            BusinessError,
        ]
        for cls in error_classes:
            assert issubclass(cls, AppError), f"{cls.__name__} should inherit from AppError"
