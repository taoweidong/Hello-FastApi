"""公共验证器的单元测试。"""

from src.application.validators import empty_str_or_zero_to_none, empty_str_to_none, parse_status, parse_time_range


class TestEmptyStrToNone:
    """empty_str_to_none 验证器测试。"""

    def test_empty_string_returns_none(self):
        """空字符串应返回 None。"""
        assert empty_str_to_none("") is None

    def test_none_returns_none(self):
        """None 应返回 None。"""
        assert empty_str_to_none(None) is None

    def test_non_empty_string_returns_value(self):
        """非空字符串应返回原值。"""
        assert empty_str_to_none("test") == "test"

    def test_whitespace_string_returns_value(self):
        """包含空格的字符串应返回原值。"""
        assert empty_str_to_none("  test  ") == "  test  "

    def test_integer_returns_value(self):
        """整数应返回原值。"""
        assert empty_str_to_none(123) == 123

    def test_zero_returns_zero(self):
        """0 应返回 0。"""
        assert empty_str_to_none(0) == 0


class TestEmptyStrOrZeroToNone:
    """empty_str_or_zero_to_none 验证器测试。"""

    def test_empty_string_returns_none(self):
        """空字符串应返回 None。"""
        assert empty_str_or_zero_to_none("") is None

    def test_zero_returns_none(self):
        """0 应返回 None。"""
        assert empty_str_or_zero_to_none(0) is None

    def test_none_returns_none(self):
        """None 应返回 None。"""
        assert empty_str_or_zero_to_none(None) is None

    def test_string_zero_converts_to_int_zero(self):
        """字符串 '0' 会先尝试转换为 int，返回 0。"""
        # 注意：empty_str_or_zero_to_none 先检查 v == 0 (整数)
        # '0' 不是整数 0，所以会尝试 int('0') = 0
        # 然后 0 被检查是否 == 0，但已经返回了
        # 实际行为：'0' -> int('0') = 0 -> 返回 0（因为在检查 v == 0 之后才进行 int 转换）
        result = empty_str_or_zero_to_none("0")
        # 根据实现，'0' 会被转换为 int 0
        assert result == 0

    def test_positive_integer_returns_value(self):
        """正整数应返回原值。"""
        assert empty_str_or_zero_to_none(123) == 123

    def test_negative_integer_returns_value(self):
        """负整数应返回原值。"""
        assert empty_str_or_zero_to_none(-1) == -1

    def test_string_number_converts_to_int(self):
        """数字字符串应转换为整数。"""
        assert empty_str_or_zero_to_none("123") == 123

    def test_invalid_string_returns_none(self):
        """无效的字符串应返回 None。"""
        assert empty_str_or_zero_to_none("abc") is None


class TestParseTimeRange:
    """parse_time_range 工具函数测试。"""

    def test_valid_time_range(self):
        """有效的时间范围应返回元组。"""
        start = "2026-01-01T00:00:00"
        end = "2026-01-31T23:59:59"
        result = parse_time_range([start, end])
        assert result == (start, end)

    def test_none_returns_none_tuple(self):
        """None 应返回 (None, None)。"""
        assert parse_time_range(None) == (None, None)

    def test_empty_list_returns_none_tuple(self):
        """空列表应返回 (None, None)。"""
        assert parse_time_range([]) == (None, None)

    def test_single_element_returns_none_tuple(self):
        """单元素列表应返回 (None, None)。"""
        assert parse_time_range(["2026-01-01"]) == (None, None)

    def test_three_elements_returns_none_tuple(self):
        """三元素列表不符合长度要求，返回 (None, None)。"""
        # parse_time_range 只接受恰好两个元素的列表
        result = parse_time_range(["a", "b", "c"])
        assert result == (None, None)


class TestParseStatus:
    """parse_status 工具函数测试。"""

    def test_none_returns_none(self):
        """None 应返回 None。"""
        assert parse_status(None) is None

    def test_empty_string_returns_none(self):
        """空字符串应返回 None。"""
        assert parse_status("") is None

    def test_integer_returns_integer(self):
        """整数应返回原值。"""
        assert parse_status(1) == 1
        assert parse_status(0) == 0

    def test_string_number_converts(self):
        """数字字符串应转换为整数。"""
        assert parse_status("1") == 1
        assert parse_status("0") == 0

    def test_invalid_string_returns_none(self):
        """无效字符串应返回 None。"""
        assert parse_status("abc") is None
