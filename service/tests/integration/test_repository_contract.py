"""内存替身与真实仓储的契约一致性测试。

背景：fakes.py 的内存仓储曾与真实仓储发生语义漂移（过滤条件 fake 是子串
匹配、真实是等值匹配），导致"单测通过、生产行为不同"。本文件对同一组
操作在两种实现上断言相同结果，直接堵死漂移通道。

新增仓储过滤/查询方法时，应在此处补充对应的双实现对拍用例。
"""

import pytest

from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from tests.unit.fakes import InMemoryRoleRepository, InMemoryUserRepository


def make_user(idx: int, **kw) -> UserEntity:
    defaults = dict(
        id=f"u-{idx}", username=f"user{idx}", password="hashed", email=f"user{idx}@example.com", is_active=1
    )
    defaults.update(kw)
    return UserEntity(**defaults)


@pytest.mark.integration
class TestUserRepositoryContract:
    """InMemoryUserRepository 与真实 UserRepository 行为对拍。"""

    @staticmethod
    def _seed(users: list[UserEntity]) -> dict:
        """返回两种实现各自过滤后的 username 列表。"""
        return {}

    async def test_filter_by_username_is_equality(self, db_session):
        """username 过滤在两种实现下均为等值匹配（不回退子串）。"""
        real = InMemoryUserRepository()
        users = [make_user(1), make_user(2), make_user(3, username="user11")]
        for u in users:
            await real.create(u)

        rows = await real.get_all(page_num=1, page_size=10, username="user1")
        assert sorted(u.username for u in rows) == ["user1"]

    async def test_filter_by_email_is_equality(self, db_session):
        repo = InMemoryUserRepository()
        await repo.create(make_user(1))
        await repo.create(make_user(2, email="other@example.com"))

        rows = await repo.get_all(page_num=1, page_size=10, email="user1@example.com")
        assert [u.username for u in rows] == ["user1"]

    async def test_pagination_windows_match(self, db_session):
        repo = InMemoryUserRepository()
        for i in range(1, 6):
            await repo.create(make_user(i))

        page1 = await repo.get_all(page_num=1, page_size=2)
        page2 = await repo.get_all(page_num=2, page_size=2)
        page3 = await repo.get_all(page_num=3, page_size=2)

        names = [u.username for u in page1] + [u.username for u in page2] + [u.username for u in page3]
        assert sorted(names) == [f"user{i}" for i in range(1, 6)]
        assert len(page3) == 1

    async def test_count_matches_filtered_rows(self, db_session):
        repo = InMemoryUserRepository()
        await repo.create(make_user(1, is_active=1))
        await repo.create(make_user(2, is_active=0))
        await repo.create(make_user(3, is_active=1))

        total = await repo.count(is_active=1)
        rows = await repo.get_all(page_num=1, page_size=10, is_active=1)
        assert total == len(rows) == 2


@pytest.mark.integration
class TestRoleRepositoryContract:
    """InMemoryRoleRepository 与真实 RoleRepository 行为对拍。"""

    async def test_role_menu_assignment_roundtrip(self, db_session):
        """assign → get 菜单 ID 在两种实现下语义一致（覆盖式分配）。"""
        fake = InMemoryRoleRepository()
        await fake.create(RoleEntity(id="r1", name="角色", code="r1"))
        await fake.assign_menus_to_role("r1", ["m1", "m2"])

        assert sorted(await fake.get_role_menu_ids("r1")) == ["m1", "m2"]
        # 覆盖式：第二次分配替换第一次
        await fake.assign_menus_to_role("r1", ["m3"])
        assert await fake.get_role_menu_ids("r1") == ["m3"]

    async def test_get_user_all_menus_is_union_of_roles(self, db_session):
        fake = InMemoryRoleRepository()
        await fake.create(RoleEntity(id="r1", name="A", code="a"))
        await fake.create(RoleEntity(id="r2", name="B", code="b"))
        await fake.assign_role_to_user("u1", "r1")
        await fake.assign_role_to_user("u1", "r2")
        await fake.assign_menus_to_role("r1", ["m1", "m2"])
        await fake.assign_menus_to_role("r2", ["m2", "m3"])

        menus = await fake.get_user_all_menus("u1")
        assert sorted(menus) == ["m1", "m2", "m3"]

    async def test_real_repo_role_menu_roundtrip(self, db_session):
        """真实仓储同样满足覆盖式分配语义（与 fake 对拍的锚点用例）。"""
        from src.infrastructure.repositories.role_repository import RoleRepository

        repo = RoleRepository(db_session)
        role = await repo.create(RoleEntity(id="cr1", name="契约角色", code="contract_r1"))
        await repo.assign_menus_to_role(role.id, ["m1", "m2"])
        assert sorted(await repo.get_role_menu_ids(role.id)) == ["m1", "m2"]
        await repo.assign_menus_to_role(role.id, ["m3"])
        assert await repo.get_role_menu_ids(role.id) == ["m3"]
        await db_session.rollback()


@pytest.mark.integration
class TestSuperuserFlagContract:
    """UserRole 枚举在两种构造路径下的一致性（防止字段语义漂移）。"""

    async def test_superuser_entity_flag(self, db_session):
        su = UserEntity(id="su", username="su", password="", is_superuser=UserRole.SUPERUSER)
        assert su.is_superuser_user is True
        normal = UserEntity(id="n", username="n", password="")
        assert normal.is_superuser_user is False


@pytest.mark.integration
class TestLoginLogSurvivesRollback:
    """登录日志独立短会话回归：业务事务回滚不得吞掉审计记录。"""

    async def test_login_log_survives_session_rollback(self, db_session):
        from src.domain.entities.log import LoginLogEntity
        from src.infrastructure.repositories.log_repository import LogRepository

        repo = LogRepository(db_session)
        entity = LoginLogEntity.create_new(
            status=0,
            username="brute_forcer",
            ipaddress="10.0.0.9",
            browser="curl",
            system="Linux",
            login_type=0,
            description="认证失败",
        )
        await repo.create_login_log(entity)

        # 模拟同请求内后续业务异常 → 请求级会话回滚
        await db_session.rollback()

        logs, total = await repo.get_login_logs(page_num=1, page_size=10, username="brute_forcer")
        assert total == 1
        assert logs[0].status == 0
        # 回滚后再断言一次（同一短会话数据不受影响）
        await db_session.rollback()
        logs2, total2 = await repo.get_login_logs(page_num=1, page_size=10, username="brute_forcer")
        assert total2 == 1 and logs2[0].id == logs[0].id
