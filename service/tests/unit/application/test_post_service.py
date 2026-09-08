"""PostService 岗位应用服务单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.post_dto import PostCreateDTO, PostListQueryDTO, PostUpdateDTO
from src.application.services.post_service import PostService
from src.domain.entities.post import PostEntity
from src.domain.entities.user import UserEntity
from src.domain.exceptions import ConflictError, NotFoundError


def _make_user() -> UserEntity:
    """构造测试用当前用户实体。"""
    return UserEntity(id="user-1", username="admin", password="", nickname="管理员")


def _make_post(**overrides) -> PostEntity:
    """构造测试用岗位实体。"""
    base = dict(id="post-1", post_code="ceo", post_name="董事长", post_sort=1, is_active=1)
    base.update(overrides)
    return PostEntity(**base)


@pytest.mark.unit
class TestPostService:
    """岗位服务逻辑测试。"""

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo):
        return PostService(post_repo=mock_repo)

    async def test_create_post_conflict_on_duplicate_code(self, service, mock_repo):
        """岗位编码已存在时抛出 ConflictError。"""
        mock_repo.get_by_code = AsyncMock(return_value=_make_post())
        with pytest.raises(ConflictError):
            await service.create_post(PostCreateDTO(postCode="ceo", postName="董事长"), _make_user())

    async def test_create_post_records_creator(self, service, mock_repo):
        """创建成功时记录创建人ID。"""
        mock_repo.get_by_code = AsyncMock(return_value=None)
        mock_repo.create = AsyncMock(side_effect=lambda e: e)

        result = await service.create_post(PostCreateDTO(postCode="dev", postName="工程师"), _make_user())

        assert result.postCode == "dev"
        assert result.postName == "工程师"
        assert result.creatorId == "user-1"
        assert result.isActive == 1

    async def test_get_post_not_found(self, service, mock_repo):
        """岗位不存在时抛出 NotFoundError。"""
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await service.get_post("missing")

    async def test_get_posts_returns_dto_and_total(self, service, mock_repo):
        """列表查询返回响应 DTO 列表与总数。"""
        mock_repo.count = AsyncMock(return_value=2)
        mock_repo.get_all = AsyncMock(return_value=[_make_post(), _make_post(id="post-2", post_code="dev")])

        result, total = await service.get_posts(PostListQueryDTO(postCode="c"))

        assert total == 2
        assert [p.postCode for p in result] == ["ceo", "dev"]
        mock_repo.count.assert_awaited_once_with(post_code="c", post_name=None, is_active=None)

    async def test_get_active_post_options(self, service, mock_repo):
        """下拉选项仅返回启用岗位并转换为 camelCase 字段。"""
        mock_repo.get_all_active = AsyncMock(return_value=[_make_post()])

        result = await service.get_active_post_options()

        assert result == [{"id": "post-1", "postCode": "ceo", "postName": "董事长", "postSort": 1}]

    async def test_update_post_records_modifier(self, service, mock_repo):
        """更新时应用字段变更并记录修改人。"""
        mock_repo.get_by_id = AsyncMock(return_value=_make_post())
        mock_repo.get_by_code = AsyncMock(return_value=None)
        mock_repo.update = AsyncMock(side_effect=lambda e: e)

        result = await service.update_post("post-1", PostUpdateDTO(postName="总经理", isActive=0), _make_user())

        assert result.postName == "总经理"
        assert result.isActive == 0
        assert result.modifierId == "user-1"

    async def test_update_post_conflict_on_other_code(self, service, mock_repo):
        """更新编码与其他岗位冲突时抛出 ConflictError。"""
        mock_repo.get_by_id = AsyncMock(return_value=_make_post())
        mock_repo.get_by_code = AsyncMock(return_value=_make_post(id="post-other"))
        with pytest.raises(ConflictError):
            await service.update_post("post-1", PostUpdateDTO(postCode="dev"), _make_user())

    async def test_update_post_not_found(self, service, mock_repo):
        """更新不存在的岗位抛出 NotFoundError。"""
        mock_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await service.update_post("missing", PostUpdateDTO(postName="x"), _make_user())

    async def test_delete_post_not_found(self, service, mock_repo):
        """删除不存在的岗位抛出 NotFoundError。"""
        mock_repo.delete = AsyncMock(return_value=False)
        with pytest.raises(NotFoundError):
            await service.delete_post("missing")

    async def test_batch_delete_returns_counts(self, service, mock_repo):
        """批量删除返回实际删除数与请求数。"""
        mock_repo.batch_delete = AsyncMock(return_value=1)

        result = await service.batch_delete_posts(["a", "b"])

        assert result == {"deleted_count": 1, "total_requested": 2}
