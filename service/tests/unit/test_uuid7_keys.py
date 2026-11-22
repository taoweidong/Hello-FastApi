"""UUIDv7 主键生成器（uuid_utils.compat.uuid7）的行为回归测试。

主键策略见 src/infrastructure/database/models/__init__.py 的说明：
应用侧生成保证 SQLite/PostgreSQL 双轨一致，时间有序改善 B-tree 局部性；
存量 uuid4 主键不回填。
"""

import time
from uuid import RFC_4122

from uuid_utils.compat import uuid7

_HEX_CHARS = set("0123456789abcdef")


def test_uuid7_hex_format():
    """32 位 hex 主键：长度与小写十六进制字符集校验。"""
    key = uuid7().hex
    assert len(key) == 32
    assert set(key) <= _HEX_CHARS


def test_uuid7_version_and_variant():
    """RFC 9562：版本号 nibble 为 7，变体位为 RFC 4122。"""
    u = uuid7()
    assert u.version == 7
    assert u.variant == RFC_4122


def test_uuid7_time_field_matches_current_epoch():
    """时间字段（前 48bit 毫秒时间戳）应接近当前系统时间。"""
    ts_ms = int(uuid7().hex[:12], 16)
    now_ms = int(time.time() * 1000)
    assert abs(ts_ms - now_ms) < 5000


def test_uuid7_dashed_str_format():
    """36 位带横线主键格式（post/notice/role_dept_link 等表）。"""
    s = str(uuid7())
    assert len(s) == 36
    assert s.count("-") == 4
    assert s[14] == "7"  # 版本号 nibble
    assert set(s.replace("-", "")) <= _HEX_CHARS


def test_uuid7_time_field_monotonic_in_process():
    """同毫秒内 rand 段允许无序，但时间字段（前 48bit）单调不减。"""
    keys = [uuid7() for _ in range(64)]
    times = [int(k.hex[:12], 16) for k in keys]
    assert all(t2 >= t1 for t1, t2 in zip(times, times[1:], strict=False))


def test_model_primary_keys_use_uuid7():
    """表模型 default_factory 实际产出 UUIDv7（32 位 hex 与 36 位两种形态）。"""
    from src.infrastructure.database.models import Notice, User

    user_id = User(password="x").id
    assert len(user_id) == 32
    assert int(user_id[12], 16) == 7

    notice_id = Notice(title="t").id
    assert len(notice_id) == 36
    assert notice_id[14] == "7"
