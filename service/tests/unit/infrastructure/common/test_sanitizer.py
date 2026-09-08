"""数据脱敏工具测试。"""

from src.infrastructure.common.sanitizer import DataSanitizer, safe_log_data


class TestSanitizeDict:
    """sanitize_dict 测试。"""

    def test_sanitize_dict_with_sensitive_key(self):
        """测试字典包含敏感键值。"""
        data = {"username": "admin", "password": "secret123"}
        result = DataSanitizer.sanitize_dict(data)
        assert result["username"] == "admin"
        assert result["password"] == "********"

    def test_sanitize_dict_with_nested_dict(self):
        """测试字典包含嵌套字典。"""
        data = {"config": {"db_password": "mypassword", "host": "localhost"}}
        result = DataSanitizer.sanitize_dict(data)
        assert result["config"]["host"] == "localhost"
        assert result["config"]["db_password"] == "********"

    def test_sanitize_dict_with_nested_dict_and_sensitive_value_being_dict(self):
        """测试字典 value 为含敏感键的 dict，嵌套 sanitize_dict 命中敏感键检测与掩码。"""
        data = {"wrapper_key": {"inner_password": "abc123abc123", "normal": "ok"}}
        result = DataSanitizer.sanitize_dict(data)
        # The inner dict gets sanitized via sanitize_dict -> _is_sensitive_key on "inner_password" -> _mask_value
        assert result["wrapper_key"]["normal"] == "ok"
        assert result["wrapper_key"]["inner_password"] == "********"

    def test_sanitize_dict_with_list_value(self):
        """测试字典的 value 是 list → hits L46 (sanitize_list called from sanitize_dict)."""
        data = {"users": [{"name": "alice", "token": "secret_token"}, {"name": "bob", "role": "user"}], "count": 2}
        result = DataSanitizer.sanitize_dict(data)
        assert result["count"] == 2
        assert result["users"][0]["name"] == "alice"
        assert result["users"][0]["token"] == "********"
        assert result["users"][1]["role"] == "user"

    def test_sanitize_dict_with_custom_mask_char(self):
        """测试自定义脱敏字符。"""
        data = {"api_key": "topsecret"}
        result = DataSanitizer.sanitize_dict(data, mask_char="#")
        assert result["api_key"] == "########"

    def test_sanitize_dict_plain(self):
        """测试不包含敏感信息的字典。"""
        data = {"name": "test", "value": 42}
        result = DataSanitizer.sanitize_dict(data)
        assert result == {"name": "test", "value": 42}


class TestSanitizeList:
    """sanitize_list 测试。"""

    def test_sanitize_list_with_dicts(self):
        """测试列表包含字典元素。"""
        data = [{"username": "alice", "token": "abc123abc123"}]
        result = DataSanitizer.sanitize_list(data)
        assert result[0]["username"] == "alice"
        assert result[0]["token"] == "********"

    def test_sanitize_list_with_primitives(self):
        """测试列表包含基本类型元素。"""
        data = ["hello", 42, True]
        result = DataSanitizer.sanitize_list(data)
        assert result == ["hello", 42, True]

    def test_sanitize_list_nested(self):
        """测试嵌套列表 (list of lists) → hits L66-69。"""
        data = [[{"name": "item1", "secret": "hiddenvalue12"}, "plain_string"], [1, 2, 3]]
        result = DataSanitizer.sanitize_list(data)
        # Nested list element with dict
        assert result[0][0]["name"] == "item1"
        assert result[0][0]["secret"] == "********"
        assert result[0][1] == "plain_string"
        # Nested list with primitives
        assert result[1] == [1, 2, 3]


class TestSanitizeString:
    """sanitize_string 测试。"""

    def test_sanitize_string_with_default_patterns(self):
        """测试使用默认模式脱敏字符串 → hits L83-86 (sensitive_patterns is None)。"""
        data = "password: mysecret123 token=abc123"
        result = DataSanitizer.sanitize_string(data)
        assert "password: ********" in result
        assert "token: ********" in result

    def test_sanitize_string_with_custom_patterns(self):
        """测试使用自定义模式脱敏字符串。"""
        import re

        custom_patterns = [re.compile(r"phone", re.IGNORECASE)]
        data = 'phone: "13800138000"'
        result = DataSanitizer.sanitize_string(data, sensitive_patterns=custom_patterns)
        assert "phone: ********" in result


class TestMaskValue:
    """_mask_value 测试。"""

    def test_mask_value_none(self):
        """测试 None 值 → hits L118-119."""
        result = DataSanitizer._mask_value(None)
        assert result is None

    def test_mask_value_show_length(self):
        """测试 show_length=True 显示最后 2 个字符 → hits L122-123."""
        result = DataSanitizer._mask_value("abcdefgh", "*", show_length=True)
        assert result == "******gh"

    def test_mask_value_default(self):
        """测试默认的 min(len, 8) 路径 → hits L124."""
        # Short value
        result_short = DataSanitizer._mask_value("abc")
        assert result_short == "***"
        # Long value (capped at 8)
        result_long = DataSanitizer._mask_value("secret123456")
        assert result_long == "********"

    def test_mask_value_sensitive_key_in_dict(self):
        """测试在 sanitize_dict 中调用 _mask_value 处理敏感键值 → hits L42."""
        data = {"password": "mysecret"}
        result = DataSanitizer.sanitize_dict(data)
        assert result["password"] == "********"

    def test_mask_value_with_custom_mask_char(self):
        """测试自定义脱敏字符。"""
        result = DataSanitizer._mask_value("password123", "#")
        assert result == "########"


class TestSafeLogData:
    """safe_log_data 测试。"""

    def test_safe_log_data_dict(self):
        """测试字典输入。"""
        data = {"username": "admin", "password": "secret123456"}
        result = safe_log_data(data)
        assert isinstance(result, dict)
        assert result["password"] == "********"

    def test_safe_log_data_list(self):
        """测试列表输入 → hits L152."""
        data = [{"password": "secret123"}, {"name": "ok"}]
        result = safe_log_data(data)
        assert isinstance(result, list)
        assert result[0]["password"] == "********"
        assert result[1]["name"] == "ok"

    def test_safe_log_data_string(self):
        """测试字符串输入 → hits L156."""
        data = "token: abc123"
        result = safe_log_data(data)
        assert isinstance(result, str)
        assert "token: ********" in result

    def test_safe_log_data_exception(self):
        """测试异常输入 → hits L157-158 (Exception branch in safe_log_data, L160)."""
        exc = ValueError("password=secretvalue123")
        result = safe_log_data(exc)
        assert isinstance(result, str)
        assert "password: ********" in result

    def test_safe_log_data_other(self):
        """测试其他类型输入 (int, bool, etc.) — hits the else branch (not listed as missed but good to cover)."""
        result = safe_log_data(42)
        assert result == 42

        result = safe_log_data(True)
        assert result is True

    def test_safe_log_data_list_with_error(self):
        """测试 safe_log_data 中 list 分支处理嵌套数据 → L152 with nested dicts."""
        data = [{"token": "abcabcabc", "nested": [{"pwd": "pwdvalue123"}]}]
        result = safe_log_data(data)
        assert isinstance(result, list)
        assert result[0]["token"] == "********"
        assert result[0]["nested"][0]["pwd"] == "********"
