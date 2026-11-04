"""NoticeDTO 单元测试。

重点回归：content 设置 max_length 上限，防止超大公告经 WS 全员广播。
"""

import pytest
from pydantic import ValidationError

from src.application.dto.notice_dto import NoticeCreateDTO, NoticeUpdateDTO


@pytest.mark.unit
class TestNoticeCreateDTO:
    """公告创建 DTO 测试。"""

    def test_valid_payload(self):
        dto = NoticeCreateDTO(title="公告", content="正文", noticeType=2, isActive=1)
        assert dto.title == "公告"
        assert dto.content == "正文"
        assert dto.noticeType == 2

    def test_content_default_empty(self):
        dto = NoticeCreateDTO(title="公告")
        assert dto.content == ""

    def test_rejects_empty_title(self):
        with pytest.raises(ValidationError):
            NoticeCreateDTO(title="")

    def test_rejects_oversize_content(self):
        """超过 65535 字符的内容必须被拒绝（防超大广播）。"""
        with pytest.raises(ValidationError):
            NoticeCreateDTO(title="公告", content="x" * 65536)

    def test_accepts_max_length_content(self):
        dto = NoticeCreateDTO(title="公告", content="x" * 65535)
        assert len(dto.content) == 65535

    def test_rejects_invalid_notice_type(self):
        with pytest.raises(ValidationError):
            NoticeCreateDTO(title="公告", noticeType=3)

    def test_rejects_invalid_is_active(self):
        with pytest.raises(ValidationError):
            NoticeCreateDTO(title="公告", isActive=2)


@pytest.mark.unit
class TestNoticeUpdateDTO:
    """公告更新 DTO 测试。"""

    def test_all_fields_optional(self):
        dto = NoticeUpdateDTO()
        assert dto.title is None
        assert dto.content is None

    def test_rejects_oversize_content(self):
        with pytest.raises(ValidationError):
            NoticeUpdateDTO(content="x" * 65536)
