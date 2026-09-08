"""用户应用服务 — 真实业务逻辑单元测试。

与既有的 ``tests/unit/test_user_service.py``（使用 ``AsyncMock`` 替换仓储，
只断言「mock 被以某种方式调用」）不同，本文件使用仓储接口的**内存实现**，
在仅替换基础设施边界的前提下验证**真实业务语义**：

- 用户名 / 邮箱唯一性冲突
- 状态机变更（启用 / 禁用）
- 密码哈希与旧密码校验
- 批量删除的计数与缓存失效次数
- 超级用户保护的越权防护

这些正是 mock 型测试无法覆盖、而集成测试又过于昂贵的核心业务规则。
"""

from __future__ import annotations

import pytest

from src.application.dto.user_dto import (
    ChangePasswordDTO,
    UserCreateDTO,
    UserListQueryDTO,
    UserUpdateDTO,
)
from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole, UserStatus
from src.domain.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from src.domain.services.password_service import PasswordService
from src.application.services.user_service import UserService
from tests.unit.fakes import InMemoryRoleRepository, InMemoryUserRepository, RecordingCacheService


@pytest.fixture
def password_service() -> PasswordService:
    return PasswordService()


@pytest.fixture
def user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def role_repo() -> InMemoryRoleRepository:
    return InMemoryRoleRepository()


@pytest.fixture
def cache() -> RecordingCacheService:
    return RecordingCacheService()


@pytest.fixture
def user_service(user_repo, role_repo, password_service, cache) -> UserService:
    return UserService(repo=user_repo, password_service=password_service, role_repo=role_repo, cache_service=cache)


def make_user(
    username: str = "alice",
    email: str = "alice@example.com",
    *,
    is_superuser: bool = False,
    is_active: bool = True,
) -> UserEntity:
    """构造一个测试用户实体。"""
    return UserEntity.create_new(
        username=username,
        hashed_password="hashed",
        email=email,
        is_active=UserStatus.ACTIVE if is_active else UserStatus.INACTIVE,
        is_staff=UserRole.USER,
    )


class TestCreateUser:
    """创建用户的业务规则。"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, user_repo):
        dto = UserCreateDTO(username="bob", password="Passw0rd!", email="bob@example.com")

        result = await user_service.create_user(dto)

        assert result.username == "bob"
        assert result.email == "bob@example.com"
        # 真实落库：可通过仓储查回
        assert await user_repo.get_by_username("bob") is not None

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username_conflicts(self, user_service, user_repo):
        await user_repo.create(make_user(username="alice"))

        with pytest.raises(ConflictError, match="alice"):
            await user_service.create_user(UserCreateDTO(username="alice", password="Passw0rd!"))

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_conflicts(self, user_service, user_repo):
        await user_repo.create(make_user(username="alice", email="dup@example.com"))

        with pytest.raises(ConflictError, match="dup@example.com"):
            await user_service.create_user(UserCreateDTO(username="other", password="Passw0rd!", email="dup@example.com"))

    @pytest.mark.asyncio
    async def test_password_is_hashed_not_stored_plaintext(self, user_service, user_repo, password_service):
        await user_service.create_user(UserCreateDTO(username="bob", password="PlainText123", email="bob@example.com"))

        stored = await user_repo.get_by_username("bob")
        assert stored is not None
        assert stored.password != "PlainText123"
        assert password_service.verify_password("PlainText123", stored.password)


class TestUpdateUser:
    """更新用户的业务规则。"""

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service):
        with pytest.raises(NotFoundError):
            await user_service.update_user("missing-id", UserUpdateDTO(nickname="x"))

    @pytest.mark.asyncio
    async def test_update_user_email_conflicts_with_other_user(self, user_service, user_repo):
        alice = make_user(username="alice", email="alice@example.com")
        bob = make_user(username="bob", email="bob@example.com")
        await user_repo.create(alice)
        await user_repo.create(bob)

        with pytest.raises(ConflictError):
            await user_service.update_user(bob.id, UserUpdateDTO(email="alice@example.com"))

    @pytest.mark.asyncio
    async def test_update_user_own_email_allowed(self, user_service, user_repo):
        alice = make_user(username="alice", email="alice@example.com")
        await user_repo.create(alice)

        result = await user_service.update_user(alice.id, UserUpdateDTO(email="alice@example.com", nickname="Alice"))

        assert result.nickname == "Alice"


class TestUserStatus:
    """用户状态机。"""

    @pytest.mark.asyncio
    async def test_deactivate_then_activate(self, user_service, user_repo):
        alice = make_user()
        await user_repo.create(alice)

        await user_service.update_status(alice.id, 0)
        assert (await user_repo.get_by_id(alice.id)).is_active == UserStatus.INACTIVE

        await user_service.update_status(alice.id, 1)
        assert (await user_repo.get_by_id(alice.id)).is_active == UserStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, user_service):
        with pytest.raises(NotFoundError):
            await user_service.update_status("missing", 1)


class TestPasswordManagement:
    """密码管理。"""

    @pytest.mark.asyncio
    async def test_reset_password_replaces_hash(self, user_service, user_repo, password_service):
        alice = make_user()
        await user_repo.create(alice)

        await user_service.reset_password(alice.id, "NewPass123")

        stored = await user_repo.get_by_id(alice.id)
        assert password_service.verify_password("NewPass123", stored.password)

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password_rejected(self, user_service, user_repo, password_service):
        alice = make_user()
        alice.password = password_service.hash_password("OldPass123")
        await user_repo.create(alice)

        with pytest.raises(UnauthorizedError):
            await user_service.change_password(alice.id, ChangePasswordDTO(oldPassword="WrongPass", newPassword="NewPass123"))

    @pytest.mark.asyncio
    async def test_change_password_success(self, user_service, user_repo, password_service):
        alice = make_user()
        alice.password = password_service.hash_password("OldPass123")
        await user_repo.create(alice)

        await user_service.change_password(alice.id, ChangePasswordDTO(oldPassword="OldPass123", newPassword="NewPass456"))

        stored = await user_repo.get_by_id(alice.id)
        assert password_service.verify_password("NewPass456", stored.password)


class TestSuperuserProtection:
    """P0 安全修复：超级用户账号只能被超级用户操作。"""

    @pytest.mark.asyncio
    async def test_non_superuser_cannot_reset_superuser_password(self, user_service, user_repo):
        admin = make_user(username="root")
        admin.is_superuser = UserRole.SUPERUSER
        await user_repo.create(admin)

        with pytest.raises(ForbiddenError):
            await user_service.reset_password(admin.id, "Hacked123", operator_is_superuser=False)

    @pytest.mark.asyncio
    async def test_superuser_can_reset_superuser_password(self, user_service, user_repo, password_service):
        admin = make_user(username="root")
        admin.is_superuser = UserRole.SUPERUSER
        await user_repo.create(admin)

        await user_service.reset_password(admin.id, "AdminPass123", operator_is_superuser=True)

        assert password_service.verify_password("AdminPass123", (await user_repo.get_by_id(admin.id)).password)

    @pytest.mark.asyncio
    async def test_non_superuser_can_reset_normal_user_password(self, user_service, user_repo, password_service):
        alice = make_user()
        await user_repo.create(alice)

        # 普通管理员操作普通用户应当放行
        await user_service.reset_password(alice.id, "ResetPass123", operator_is_superuser=False)

        assert password_service.verify_password("ResetPass123", (await user_repo.get_by_id(alice.id)).password)

    @pytest.mark.asyncio
    async def test_non_superuser_cannot_disable_superuser(self, user_service, user_repo):
        admin = make_user(username="root")
        admin.is_superuser = UserRole.SUPERUSER
        await user_repo.create(admin)

        with pytest.raises(ForbiddenError):
            await user_service.update_status(admin.id, 0, operator_is_superuser=False)

        # 状态未被修改
        assert (await user_repo.get_by_id(admin.id)).is_active == UserStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_non_superuser_cannot_assign_roles_to_superuser(self, user_service, user_repo):
        admin = make_user(username="root")
        admin.is_superuser = UserRole.SUPERUSER
        await user_repo.create(admin)

        with pytest.raises(ForbiddenError):
            await user_service.assign_roles(admin.id, ["role-1"], operator_is_superuser=False)


class TestBatchDeleteAndCache:
    """批量删除的计数语义与缓存失效次数。"""

    @pytest.mark.asyncio
    async def test_batch_delete_counts_only_existing(self, user_service, user_repo):
        users = [make_user(username=f"u{i}", email=f"u{i}@example.com") for i in range(3)]
        for u in users:
            await user_repo.create(u)
        ids = [u.id for u in users] + ["ghost-id"]

        result = await user_service.batch_delete_users(ids)

        assert result["deleted_count"] == 3
        assert result["total_requested"] == 4
        assert await user_repo.get_by_id(users[0].id) is None

    @pytest.mark.asyncio
    async def test_batch_delete_invalidates_cache_once(self, user_service, user_repo, cache):
        """批量删除应触发一次批量失效，而非 N 次单点失效。"""
        users = [make_user(username=f"u{i}", email=f"u{i}@example.com") for i in range(5)]
        for u in users:
            await user_repo.create(u)

        await user_service.batch_delete_users([u.id for u in users])

        assert len(cache.batch_calls) == 1
        assert len(cache.batch_calls[0]) == 5
        # 不应退化为逐条失效
        assert cache.invalidate_user_info_calls == []

    @pytest.mark.asyncio
    async def test_single_delete_invalidates_single_user_cache(self, user_service, user_repo, cache):
        alice = make_user()
        await user_repo.create(alice)

        await user_service.delete_user(alice.id)

        assert cache.invalidate_user_info_calls == [alice.id]
        assert cache.invalidate_user_permissions_calls == [alice.id]


class TestUserList:
    """用户列表的分页与筛选。"""

    @pytest.mark.asyncio
    async def test_list_returns_page_and_total(self, user_service, user_repo):
        for i in range(12):
            await user_repo.create(make_user(username=f"user{i:02d}", email=f"user{i:02d}@example.com"))

        rows, total = await user_service.get_users(UserListQueryDTO(pageNum=1, pageSize=5))

        assert total == 12
        assert len(rows) == 5

    @pytest.mark.asyncio
    async def test_list_filters_by_username(self, user_service, user_repo):
        await user_repo.create(make_user(username="alice", email="a@example.com"))
        await user_repo.create(make_user(username="bob", email="b@example.com"))

        rows, total = await user_service.get_users(UserListQueryDTO(pageNum=1, pageSize=10, username="ali"))

        assert total == 1
        assert rows[0].username == "alice"

    @pytest.mark.asyncio
    async def test_list_filters_by_active_status(self, user_service, user_repo):
        await user_repo.create(make_user(username="active1", email="a1@example.com", is_active=True))
        await user_repo.create(make_user(username="inactive1", email="i1@example.com", is_active=False))

        rows, total = await user_service.get_users(UserListQueryDTO(pageNum=1, pageSize=10, isActive=0))

        assert total == 1
        assert rows[0].username == "inactive1"
