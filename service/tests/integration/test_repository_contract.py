"""内存替身与真实仓储的契约一致性测试（真对拍）。

背景：fakes.py 的内存仓储曾与真实仓储发生语义漂移（过滤条件 fake 是子串
匹配、真实是等值匹配），导致"单测通过、生产行为不同"。

本文件的定义：对**同一组种子与操作序列**分别在 fake 与真实仓储上执行，
断言两者的可观测结果完全一致——任何一侧单独正确都不算通过。
新增仓储过滤/查询方法时，应在此处补充对应的双实现对拍场景。
"""

import pytest

from src.domain.entities.menu import MenuEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import MenuType, UserRole
from tests.unit.fakes import InMemoryRoleRepository, InMemoryUserRepository


def make_user(idx: int, **kw) -> UserEntity:
    defaults = dict(
        id=f"u-{idx}", username=f"user{idx}", password="hashed", email=f"user{idx}@example.com", is_active=1
    )
    defaults.update(kw)
    return UserEntity(**defaults)


# 用户仓储对拍场景：同一组种子 + 操作，分别在两种实现上执行
async def _collect_page_usernames(repo) -> list[str]:
    names: list[str] = []
    for page in (1, 2, 3):
        rows = await repo.get_all(page_num=page, page_size=2)
        names.extend(u.username for u in rows)
    return names


async def _run_user_scenario(make_repo) -> dict:
    repo = make_repo()
    seed = [
        make_user(1),
        make_user(2),
        make_user(3, username="user11"),
        make_user(4, is_active=0),
        make_user(5, email="other@example.com"),
    ]
    for u in seed:
        await repo.create(u)

    return {
        # 等值匹配语义（历史上 fake 曾漂移为子串匹配）
        "filter_username": sorted(u.username for u in await repo.get_all(page_num=1, page_size=10, username="user1")),
        "filter_email": sorted(
            u.username for u in await repo.get_all(page_num=1, page_size=10, email="user1@example.com")
        ),
        "filter_active": sorted(u.username for u in await repo.get_all(page_num=1, page_size=10, is_active=1)),
        # 分页窗口覆盖
        "pages": sorted(await _collect_page_usernames(repo)),
        "count_active": await repo.count(is_active=1),
        "count_all": await repo.count(),
    }


# 角色仓储对拍场景：覆盖角色-用户/角色-菜单关联与实体语义
async def _run_role_scenario(make_repo) -> dict:
    repo = make_repo()
    await repo.create(RoleEntity(id="r1", name="角色A", code="a"))
    await repo.create(RoleEntity(id="r2", name="角色B", code="b"))
    await repo.create(RoleEntity(id="r3", name="未分配", code="c"))
    await repo.assign_role_to_user("u1", "r1")
    await repo.assign_role_to_user("u1", "r2")
    await repo.assign_menus_to_role("r1", ["m1", "m2"])
    await repo.assign_menus_to_role("r2", ["m2", "m3"])

    menus = await repo.get_user_all_menus("u1")
    return {
        # 覆盖式分配：第二次分配替换第一次
        "override_r1": sorted(await repo.get_role_menu_ids("r1")),
        "unassigned_r3": await repo.get_role_menu_ids("r3"),
        # 并集 + 实体语义（消费方按 menu_type 过滤、读取 name）
        "user_all_menu_ids": sorted(m.id for m in menus),
        "user_all_menu_types": sorted({int(m.menu_type) for m in menus}),
        "user_roles": sorted(r.code for r in await repo.get_user_roles("u1")),
    }


@pytest.mark.integration
class TestUserRepositoryContract:
    """InMemoryUserRepository ↔ 真实 UserRepository 双实现对拍。"""

    async def test_fake_matches_real(self, db_session):
        from src.infrastructure.repositories.user_repository import UserRepository

        fake_result = await _run_user_scenario(InMemoryUserRepository)
        real_result = await _run_user_scenario(lambda: UserRepository(db_session))
        assert fake_result == real_result


@pytest.mark.integration
class TestRoleRepositoryContract:
    """InMemoryRoleRepository ↔ 真实 RoleRepository 双实现对拍。"""

    async def test_fake_matches_real(self, db_session):
        from src.infrastructure.repositories.role_repository import RoleRepository

        # 真实仓储 get_user_all_menus 走 role_menu_link join menu 表，
        # 需要先落菜单行；fake 侧用实体注册表提供同样的类型语义
        menu_registry = {
            "m1": MenuEntity(id="m1", name="菜单1", menu_type=int(MenuType.PERMISSION), rank=1),
            "m2": MenuEntity(id="m2", name="菜单2", menu_type=int(MenuType.PERMISSION), rank=2),
            "m3": MenuEntity(id="m3", name="菜单3", menu_type=int(MenuType.DIRECTORY), rank=3),
        }
        from src.infrastructure.database.models import Menu

        for menu in menu_registry.values():
            # meta_id 全局唯一，需逐行区分（MenuRepository.create 会连带建 meta，
            # 这里只做 join 数据准备，直接插模型行）
            db_session.add(
                Menu(id=menu.id, name=menu.name, menu_type=menu.menu_type, rank=menu.rank, meta_id=f"meta-{menu.id}")
            )
        await db_session.flush()

        fake_result = await _run_role_scenario(lambda: InMemoryRoleRepository(menu_entities=menu_registry))
        real_result = await _run_role_scenario(lambda: RoleRepository(db_session))
        assert fake_result == real_result
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
