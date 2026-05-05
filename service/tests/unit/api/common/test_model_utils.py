"""model_utils 工具函数的单元测试。"""

from datetime import datetime, timezone

import pytest
from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from src.api.common.model_utils import (
    datetime_to_isoformat,
    datetime_to_timestamp,
    model_to_dict,
    models_to_list,
    safe_int,
    safe_str,
)


class SamplePydanticModel(BaseModel):
    """用于测试的 Pydantic 模型。"""

    name: str
    age: int = 0
    email: str | None = None


class SampleSQLModel(SQLModel, table=True):
    """用于测试的 SQLModel 模型。"""

    __tablename__ = "sample_test"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    active: bool = True
    note: str | None = None


@pytest.mark.unit
class TestModelToDict:
    """model_to_dict 函数测试。"""

    def test_none_model_returns_empty_dict(self):
        """测试 None 模型应返回空字典。"""
        result = model_to_dict(None)
        assert result == {}

    def test_pydantic_model_returns_dict(self):
        """测试 Pydantic 模型应返回正确的字典。"""
        model = SamplePydanticModel(name="test", age=25)
        result = model_to_dict(model)
        assert result == {"name": "test", "age": 25, "email": None}

    def test_sqlmodel_returns_dict(self):
        """测试 SQLModel 应返回正确的字典。"""
        model = SampleSQLModel(name="test", active=True)
        result = model_to_dict(model)
        assert "name" in result
        assert result["name"] == "test"
        assert result["active"] is True

    def test_exclude_none_removes_none_values(self):
        """测试 exclude_none=True 应移除 None 值字段。"""
        model = SamplePydanticModel(name="test", age=25)
        result = model_to_dict(model, exclude_none=True)
        assert result == {"name": "test", "age": 25}

    def test_exclude_removes_specified_fields(self):
        """测试 exclude 应移除指定字段。"""
        model = SamplePydanticModel(name="test", age=25, email="a@b.com")
        result = model_to_dict(model, exclude={"email"})
        assert result == {"name": "test", "age": 25}

    def test_exclude_and_exclude_none_combined(self):
        """测试 exclude 和 exclude_none 同时使用时均生效。"""
        model = SamplePydanticModel(name="test", age=25)
        result = model_to_dict(model, exclude_none=True, exclude={"age"})
        assert result == {"name": "test"}

    def test_object_without_dump_method_returns_empty_dict(self):
        """测试没有 model_dump 或 dict 方法的对象应返回空字典。"""

        class PlainObject:
            pass

        result = model_to_dict(PlainObject())  # type: ignore[arg-type]
        assert result == {}


@pytest.mark.unit
class TestModelsToList:
    """models_to_list 函数测试。"""

    def test_empty_list_returns_empty_list(self):
        """测试空列表应返回空列表。"""
        result = models_to_list([])
        assert result == []

    def test_single_model_list_returns_list_of_dict(self):
        """测试单个模型的列表应返回包含字典的列表。"""
        models = [SamplePydanticModel(name="a", age=1)]
        result = models_to_list(models)
        assert len(result) == 1
        assert result[0]["name"] == "a"

    def test_multiple_models_returns_list_of_dicts(self):
        """测试多个模型应返回多个字典。"""
        models = [
            SamplePydanticModel(name="a", age=1),
            SamplePydanticModel(name="b", age=2),
        ]
        result = models_to_list(models)
        assert len(result) == 2
        assert result[0]["name"] == "a"
        assert result[1]["name"] == "b"

    def test_exclude_none_passed_to_model_to_dict(self):
        """测试 exclude_none 参数应传递给 model_to_dict。"""
        models = [SamplePydanticModel(name="a", age=1)]
        result = models_to_list(models, exclude_none=True)
        assert "email" not in result[0]

    def test_exclude_passed_to_model_to_dict(self):
        """测试 exclude 参数应传递给 model_to_dict。"""
        models = [SamplePydanticModel(name="a", age=1, email="a@b.com")]
        result = models_to_list(models, exclude={"email"})
        assert "email" not in result[0]


@pytest.mark.unit
class TestDatetimeToIsoformat:
    """datetime_to_isoformat 函数测试。"""

    def test_valid_datetime_returns_isoformat(self):
        """测试有效的 datetime 应返回 ISO 格式字符串。"""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = datetime_to_isoformat(dt)
        assert result == "2024-01-15T10:30:00+00:00"

    def test_none_returns_none(self):
        """测试 None 应返回 None。"""
        result = datetime_to_isoformat(None)
        assert result is None

    def test_datetime_without_tz_returns_isoformat(self):
        """测试不带时区的 datetime 应返回 ISO 格式字符串。"""
        dt = datetime(2024, 6, 1, 12, 0, 0)
        result = datetime_to_isoformat(dt)
        assert result == "2024-06-01T12:00:00"


@pytest.mark.unit
class TestDatetimeToTimestamp:
    """datetime_to_timestamp 函数测试。"""

    def test_valid_datetime_returns_millisecond_timestamp(self):
        """测试有效的 datetime 应返回毫秒时间戳。"""
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = datetime_to_timestamp(dt)
        assert result == 1704067200000
        assert isinstance(result, int)

    def test_none_returns_none(self):
        """测试 None 应返回 None。"""
        result = datetime_to_timestamp(None)
        assert result is None

    def test_datetime_without_tz_returns_timestamp(self):
        """测试不带时区的 datetime 应返回时间戳。"""
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = datetime_to_timestamp(dt)
        assert isinstance(result, int)
        assert result > 0


@pytest.mark.unit
class TestSafeStr:
    """safe_str 函数测试。"""

    def test_none_returns_default(self):
        """测试 None 应返回默认值。"""
        result = safe_str(None)
        assert result == ""

    def test_empty_string_returns_default(self):
        """测试空字符串应返回默认值。"""
        result = safe_str("")
        assert result == ""

    def test_non_empty_string_returns_value(self):
        """测试非空字符串应返回原值。"""
        result = safe_str("hello")
        assert result == "hello"

    def test_integer_converts_to_string(self):
        """测试整数应转换为字符串。"""
        result = safe_str(123)
        assert result == "123"

    def test_custom_default_value(self):
        """测试自定义默认值应生效。"""
        result = safe_str(None, default="N/A")
        assert result == "N/A"

    def test_zero_converts_to_string(self):
        """测试 0 应转换为字符串 "0"。"""
        result = safe_str(0)
        assert result == "0"

    def test_float_converts_to_string(self):
        """测试浮点数应转换为字符串。"""
        result = safe_str(3.14)
        assert result == "3.14"


@pytest.mark.unit
class TestSafeInt:
    """safe_int 函数测试。"""

    def test_none_returns_default(self):
        """测试 None 应返回默认值 None。"""
        result = safe_int(None)
        assert result is None

    def test_none_returns_custom_default(self):
        """测试 None 应返回自定义默认值。"""
        result = safe_int(None, default=0)
        assert result == 0

    def test_integer_returns_value(self):
        """测试整数应返回原值。"""
        result = safe_int(42)
        assert result == 42

    def test_float_returns_int(self):
        """测试浮点数应转换为整数。"""
        result = safe_int(3.14)
        assert result == 3

    def test_valid_string_returns_int(self):
        """测试有效的数字字符串应转换为整数。"""
        result = safe_int("123")
        assert result == 123

    def test_invalid_string_returns_default(self):
        """测试无效的字符串应返回默认值。"""
        result = safe_int("abc")
        assert result is None

    def test_empty_string_returns_default(self):
        """测试空字符串应返回默认值。"""
        result = safe_int("")
        assert result is None

    def test_negative_integer(self):
        """测试负整数应返回原值。"""
        result = safe_int(-10)
        assert result == -10

    def test_negative_float(self):
        """测试负浮点数应转换为负整数。"""
        result = safe_int(-3.9)
        assert result == -3

    def test_non_numeric_type_returns_default(self):
        """测试无法转换的类型应返回默认值。"""
        result = safe_int(["list"])  # type: ignore[arg-type]
        assert result is None

    def test_boolean_to_int(self):
        """测试布尔值 True 应转为 1（Python 中 bool 是 int 的子类）。"""
        result = safe_int(True)  # type: ignore[arg-type]
        assert result == 1

    def test_boolean_false_to_int(self):
        """测试布尔值 False 应转为 0。"""
        result = safe_int(False)
        assert result == 0
