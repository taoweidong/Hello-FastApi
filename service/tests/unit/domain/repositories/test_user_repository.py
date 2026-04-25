"""用户仓储接口的单元测试。

测试 UserRepositoryInterface 抽象基类的方法签名和返回类型。
"""

import pytest

from src.domain.entities.user import UserEntity
from src.domain.repositories.user_repository import UserRepositoryInterface


class ConcreteUserRepository(UserRepositoryInterface):
    """用于测试的 UserRepositoryInterface 最小化具体实现。"""

    def __init__(self, session=None):
        self.session = session

    async def get_by_id(self, user_id: str) -> UserEntity | None:
        return None

    async def get_by_username(self, username: str) -> UserEntity | None:
        return None

    async def get_by_email(self, email: str) -> UserEntity | None:
        return None

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
    ) -> list[UserEntity]:
        return []

    async def create(self, user: UserEntity) -> UserEntity:
        return user

    async def update(self, user: UserEntity) -> UserEntity:
        return user

    async def delete(self, user_id: str) -> bool:
        return True

    async def count(
        self,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
    ) -> int:
        return 0

    async def batch_delete(self, user_ids: list[str]) -> int:
        return len(user_ids)

    async def update_status(self, user_id: str, is_active: int) -> bool:
        return True

    async def reset_password(self, user_id: str, hashed_password: str) -> bool:
        return True


@pytest.mark.unit
class TestUserRepositoryInterface:
    """UserRepositoryInterface 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            UserRepositoryInterface(session=None)  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        repo = ConcreteUserRepository()
        assert repo is not None
        assert isinstance(repo, UserRepositoryInterface)

    # ---- get_by_id ----

    @pytest.mark.asyncio
    async def test_get_by_id_accepts_str(self):
        """测试 get_by_id 接受字符串参数。"""
        repo = ConcreteUserRepository()
        result = await repo.get_by_id("user-1")
        assert result is None

    # ---- get_by_username ----

    @pytest.mark.asyncio
    async def test_get_by_username_accepts_str(self):
        """测试 get_by_username 接受字符串参数。"""
        repo = ConcreteUserRepository()
        result = await repo.get_by_username("admin")
        assert result is None

    # ---- get_by_email ----

    @pytest.mark.asyncio
    async def test_get_by_email_accepts_str(self):
        """测试 get_by_email 接受字符串参数。"""
        repo = ConcreteUserRepository()
        result = await repo.get_by_email("admin@example.com")
        assert result is None

    # ---- get_all ----

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        """测试 get_all 返回列表。"""
        repo = ConcreteUserRepository()
        result = await repo.get_all()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_with_all_params(self):
        """测试 get_all 接受所有可选参数。"""
        repo = ConcreteUserRepository()
        result = await repo.get_all(
            page_num=1, page_size=20, username="admin", phone="138", email="test@test.com",
            is_active=1, dept_id="dept-1",
        )
        assert isinstance(result, list)

    # ---- create ----

    @pytest.mark.asyncio
    async def test_create_returns_user_entity(self):
        """测试 create 返回用户实体。"""
        repo = ConcreteUserRepository()
        entity = UserEntity(id="user-1", username="admin", password="hashed_pwd")
        result = await repo.create(entity)
        assert isinstance(result, UserEntity)

    # ---- update ----

    @pytest.mark.asyncio
    async def test_update_returns_user_entity(self):
        """测试 update 返回用户实体。"""
        repo = ConcreteUserRepository()
        entity = UserEntity(id="user-1", username="admin", password="hashed_pwd")
        result = await repo.update(entity)
        assert isinstance(result, UserEntity)

    # ---- delete ----

    @pytest.mark.asyncio
    async def test_delete_returns_bool(self):
        """测试 delete 返回布尔值。"""
        repo = ConcreteUserRepository()
        result = await repo.delete("user-1")
        assert isinstance(result, bool)

    # ---- count ----

    @pytest.mark.asyncio
    async def test_count_returns_int(self):
        """测试 count 返回整数。"""
        repo = ConcreteUserRepository()
        result = await repo.count()
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_count_with_all_params(self):
        """测试 count 接受所有可选参数。"""
        repo = ConcreteUserRepository()
        result = await repo.count(username="admin", phone="138", email="test@test.com", is_active=1, dept_id="dept-1")
        assert isinstance(result, int)

    # ---- batch_delete ----

    @pytest.mark.asyncio
    async def test_batch_delete_returns_int(self):
        """测试 batch_delete 返回整数。"""
        repo = ConcreteUserRepository()
        result = await repo.batch_delete(["user-1", "user-2"])
        assert isinstance(result, int)
        assert result == 2

    # ---- update_status ----

    @pytest.mark.asyncio
    async def test_update_status_returns_bool(self):
        """测试 update_status 返回布尔值。"""
        repo = ConcreteUserRepository()
        result = await repo.update_status("user-1", 0)
        assert isinstance(result, bool)

    # ---- reset_password ----

    @pytest.mark.asyncio
    async def test_reset_password_returns_bool(self):
        """测试 reset_password 返回布尔值。"""
        repo = ConcreteUserRepository()
        result = await repo.reset_password("user-1", "new_hashed_pwd")
        assert isinstance(result, bool)
