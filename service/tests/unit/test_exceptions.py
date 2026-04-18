"""领域异常的单元测试。"""

from http import HTTPStatus

import pytest

from src.domain.exceptions import AppError, BusinessError, ConflictError, ForbiddenError, NotFoundError, RateLimitError, UnauthorizedError, ValidationError


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
        err = ConflictError()
        assert err.detail == "资源已存在"
        assert err.status_code == HTTPStatus.CONFLICT

    def test_inherits_app_error(self):
        assert issubclass(ConflictError, AppError)


@pytest.mark.unit
class TestUnauthorizedError:
    """UnauthorizedError 测试。"""

    def test_default_detail(self):
        err = UnauthorizedError()
        assert err.detail == "需要认证"
        assert err.status_code == HTTPStatus.UNAUTHORIZED

    def test_inherits_app_error(self):
        assert issubclass(UnauthorizedError, AppError)


@pytest.mark.unit
class TestForbiddenError:
    """ForbiddenError 测试。"""

    def test_default_detail(self):
        err = ForbiddenError()
        assert err.detail == "权限不足"
        assert err.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.unit
class TestValidationError:
    """ValidationError 测试。"""

    def test_default_detail(self):
        err = ValidationError()
        assert err.detail == "验证错误"
        assert err.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.unit
class TestRateLimitError:
    """RateLimitError 测试。"""

    def test_default_detail(self):
        err = RateLimitError()
        assert err.detail == "请求过于频繁"
        assert err.status_code == HTTPStatus.TOO_MANY_REQUESTS


@pytest.mark.unit
class TestBusinessError:
    """BusinessError 测试。"""

    def test_default_detail(self):
        err = BusinessError()
        assert err.detail == "业务错误"
        assert err.status_code == HTTPStatus.BAD_REQUEST

    def test_custom_detail(self):
        err = BusinessError("父部门不存在")
        assert err.detail == "父部门不存在"
