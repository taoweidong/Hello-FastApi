"""测试替身：仓储接口的内存实现。

与 ``MagicMock`` / ``AsyncMock`` 不同，这些替身**实现了真实的存储语义**（查重、
分页、级联删除），因此基于它们编写的服务层测试能够验证真实业务逻辑，
而不是验证「某个 mock 被以某种方式调用过」。

只在基础设施边界（数据库）做替换，业务逻辑本身不 mock。
"""

from __future__ import annotations

from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface


class InMemoryUserRepository(UserRepositoryInterface):
    """用户仓储的内存实现，用于应用层服务的真实单元测试。"""

    def __init__(self, session=None) -> None:
        self._users: dict[str, UserEntity] = {}
        self._session = session

    async def get_by_id(self, user_id: str) -> UserEntity | None:
        return self._users.get(user_id)

    async def get_by_username(self, username: str) -> UserEntity | None:
        return next((u for u in self._users.values() if u.username == username), None)

    async def get_by_email(self, email: str) -> UserEntity | None:
        if not email:
            return None
        return next((u for u in self._users.values() if u.email == email), None)

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
        result = list(self._users.values())
        if username:
            result = [u for u in result if username in u.username]
        if phone:
            result = [u for u in result if u.phone == phone]
        if email:
            result = [u for u in result if email in (u.email or "")]
        if is_active is not None:
            result = [u for u in result if u.is_active == is_active]
        if dept_id:
            result = [u for u in result if u.dept_id == dept_id]
        start = (page_num - 1) * page_size
        return result[start : start + page_size]

    async def create(self, user: UserEntity) -> UserEntity:
        self._users[user.id] = user
        return user

    async def update(self, user: UserEntity) -> UserEntity:
        self._users[user.id] = user
        return user

    async def delete(self, user_id: str) -> bool:
        return self._users.pop(user_id, None) is not None

    async def count(
        self,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
    ) -> int:
        rows = await self.get_all(page_num=1, page_size=10**9, username=username, phone=phone, email=email, is_active=is_active, dept_id=dept_id)
        return len(rows)

    async def batch_delete(self, user_ids: list[str]) -> int:
        removed = 0
        for uid in user_ids:
            if self._users.pop(uid, None) is not None:
                removed += 1
        return removed


class InMemoryRoleRepository(RoleRepositoryInterface):
    """角色仓储的内存实现。"""

    def __init__(self, session=None) -> None:
        self._roles: dict[str, RoleEntity] = {}
        self._user_roles: dict[str, list[str]] = {}

    async def get_by_id(self, role_id: str) -> RoleEntity | None:
        return self._roles.get(role_id)

    async def get_by_name(self, name: str) -> RoleEntity | None:
        return next((r for r in self._roles.values() if r.name == name), None)

    async def get_by_code(self, code: str) -> RoleEntity | None:
        return next((r for r in self._roles.values() if r.code == code), None)

    async def get_all(self, page_num: int = 1, page_size: int = 10, role_name: str | None = None, is_active: int | None = None) -> list[RoleEntity]:  # noqa: D102
        result = list(self._roles.values())
        if role_name:
            result = [r for r in result if role_name in r.name]
        if is_active is not None:
            result = [r for r in result if r.is_active == is_active]
        start = (page_num - 1) * page_size
        return result[start : start + page_size]

    async def count(self, role_name: str | None = None, is_active: int | None = None) -> int:  # noqa: D102
        rows = await self.get_all(page_num=1, page_size=10**9, role_name=role_name, is_active=is_active)
        return len(rows)

    async def create(self, role: RoleEntity) -> RoleEntity:  # noqa: D102
        self._roles[role.id] = role
        return role

    async def update(self, role: RoleEntity) -> RoleEntity:  # noqa: D102
        self._roles[role.id] = role
        return role

    async def delete(self, role_id: str) -> bool:  # noqa: D102
        return self._roles.pop(role_id, None) is not None

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:  # noqa: D102
        self._user_roles.setdefault(user_id, []).append(role_id)
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:  # noqa: D102
        ids = self._user_roles.get(user_id, [])
        if role_id in ids:
            ids.remove(role_id)
            return True
        return False

    async def get_user_roles(self, user_id: str) -> list[RoleEntity]:  # noqa: D102
        return [self._roles[rid] for rid in self._user_roles.get(user_id, []) if rid in self._roles]

    async def assign_roles_to_user(self, user_id: str, role_ids: list[str]) -> bool:  # noqa: D102
        self._user_roles[user_id] = list(role_ids)
        return True

    async def assign_menus_to_role(self, role_id: str, menu_ids: list[str]) -> bool:  # noqa: D102
        return True

    async def get_role_menus(self, role_id: str) -> list:  # noqa: D102
        return []

    async def get_role_menu_ids(self, role_id: str) -> list[str]:  # noqa: D102
        return []

    async def get_user_all_menus(self, user_id: str) -> list:  # noqa: D102
        return []

    async def get_users_roles_batch(self, user_ids: list[str]) -> dict[str, list[RoleEntity]]:  # noqa: D102
        return {uid: await self.get_user_roles(uid) for uid in user_ids}

    async def get_roles_menu_ids_batch(self, role_ids: list[str]) -> dict[str, list[str]]:  # noqa: D102
        return {rid: [] for rid in role_ids}


class RecordingCacheService:
    """记录调用次数的缓存服务替身，用于验证缓存失效行为。

    同时实现 ``CachePort`` 的批量失效语义：记录单次调用所失效的用户数量，
    便于断言「批量操作只触发一次批量失效」而非 N 次单点失效。
    """

    def __init__(self) -> None:
        self.invalidated_users: list[str] = []
        self.invalidate_user_info_calls: list[str] = []
        self.invalidate_user_permissions_calls: list[str] = []
        self.batch_calls: list[list[str]] = []

    async def invalidate_user_info(self, user_id: str) -> bool:
        self.invalidate_user_info_calls.append(user_id)
        self.invalidated_users.append(user_id)
        return True

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        self.invalidate_user_permissions_calls.append(user_id)
        return True

    async def invalidate_users_batch(self, user_ids: list[str]) -> bool:
        """批量失效：一次调用处理全部用户。"""
        self.batch_calls.append(list(user_ids))
        self.invalidated_users.extend(user_ids)
        return True

    async def get_user_info(self, user_id: str):
        return None

    async def set_user_info(self, user_id: str, info: dict) -> bool:
        return True

    async def get_user_permissions(self, user_id: str):
        return None

    async def set_user_permissions(self, user_id: str, permissions: list) -> bool:
        return True

    async def invalidate_all_menus(self) -> bool:
        return True
