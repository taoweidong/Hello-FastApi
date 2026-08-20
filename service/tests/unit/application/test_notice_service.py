"""NoticeService 通知公告应用服务单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.notice_dto import NoticeCreateDTO, NoticeListQueryDTO, NoticeUpdateDTO
from src.application.services.notice_service import NoticeService
from src.domain.entities.notice import NoticeEntity
from src.domain.entities.user import UserEntity
from src.domain.exceptions import NotFoundError


def _make_user(nickname: str = "") -> UserEntity:
    """构造测试用当前用户实体。"""
    return UserEntity(id="user-1", username="admin", password="", nickname=nickname)


def _make_notice(**overrides) -> NoticeEntity:
    """构造测试用公告实体。"""
    base = dict(id="notice-1", title="测试公告", content="内容", notice_type=1, is_active=1)
    base.update(overrides)
    return NoticeEntity(**base)


@pytest.mark.unit
class TestNoticeService:
    """通知公告服务逻辑测试。"""

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo):
        return NoticeService(notice_repo=mock_repo)

    async def test_create_notice_uses_nickname_as_publisher(self, service, mock_repo):
        """创建时优先使用昵称作为发布人名称。"""
        mock_repo.create = AsyncMock(side_effect=lambda e: e)
        dto = NoticeCreateDTO(title="发布测试", content="正文", noticeType=2, isActive=1)

        result = await service.create_notice(dto, _make_user(nickname="管理员小王"))

        assert result.title == "发布测试"
        assert result.noticeType == 2
        assert result.publisherId == "user-1"
        assert result.publisherName == "管理员小王"
        assert result.creatorId == "user-1"

    async def test_create_notice_fallback_to_username(self, service, mock_repo):
        """无昵称时发布人名称回退为用户名。"""
        mock_repo.create = AsyncMock(side_effect=lambda e: e)
        dto = NoticeCreateDTO(title="发布测试")

        result = await service.create_notice(dto, _make_user(nickname=""))

        assert result.publisherName == "admin"

    async def test_get_notice_not_found(self, service, mock_repo):
        """公告不存在时抛出 NotFoundError。"""
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await service.get_notice("missing")

    async def test_get_notices_returns_dto_and_total(self, service, mock_repo):
        """列表查询返回响应 DTO 列表与总数。"""
        mock_repo.count = AsyncMock(return_value=2)
        mock_repo.get_all = AsyncMock(return_value=[_make_notice(), _make_notice(id="notice-2", title="另一条")])

        result, total = await service.get_notices(NoticeListQueryDTO(title="测试"))

        assert total == 2
        assert [n.title for n in result] == ["测试公告", "另一条"]
        mock_repo.count.assert_awaited_once_with(title="测试", notice_type=None, is_active=None)

    async def test_get_latest_notices_only_active(self, service, mock_repo):
        """最新公告仅查询启用状态并按 limit 取数。"""
        mock_repo.get_all = AsyncMock(return_value=[_make_notice()])

        result = await service.get_latest_notices(limit=3)

        assert len(result) == 1
        mock_repo.get_all.assert_awaited_once_with(page_num=1, page_size=3, is_active=1)

    async def test_update_notice_records_modifier(self, service, mock_repo):
        """更新时应用字段变更并记录修改人。"""
        mock_repo.get_by_id = AsyncMock(return_value=_make_notice())
        mock_repo.update = AsyncMock(side_effect=lambda e: e)

        result = await service.update_notice("notice-1", NoticeUpdateDTO(title="新标题", isActive=0), _make_user())

        assert result.title == "新标题"
        assert result.isActive == 0
        assert result.modifierId == "user-1"

    async def test_update_notice_not_found(self, service, mock_repo):
        """更新不存在的公告抛出 NotFoundError。"""
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await service.update_notice("missing", NoticeUpdateDTO(title="x"), _make_user())

    async def test_delete_notice_not_found(self, service, mock_repo):
        """删除不存在的公告抛出 NotFoundError。"""
        mock_repo.delete = AsyncMock(return_value=False)
        with pytest.raises(NotFoundError):
            await service.delete_notice("missing")

    async def test_batch_delete_returns_counts(self, service, mock_repo):
        """批量删除返回实际删除数与请求数。"""
        mock_repo.batch_delete = AsyncMock(return_value=1)

        result = await service.batch_delete_notices(["a", "b"])

        assert result == {"deleted_count": 1, "total_requested": 2}
