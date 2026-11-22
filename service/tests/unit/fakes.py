"""测试替身：仓储接口的内存实现。

与 ``MagicMock`` / ``AsyncMock`` 不同，这些替身**实现了真实的存储语义**（查重、
分页、级联删除），因此基于它们编写的服务层测试能够验证真实业务逻辑，
而不是验证「某个 mock 被以某种方式调用过」。

只在基础设施边界（数据库）做替换，业务逻辑本身不 mock。
"""

from __future__ import annotations

from datetime import datetime

from src.domain.entities.log import LoginLogEntity, OperationLogEntity
from src.domain.entities.menu import MenuEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity
from src.domain.enums import DataScope
from src.domain.repositories.log_repository import LogRepositoryInterface
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.cache_port import UserCachePort


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
        scope_dept_ids: list[str] | None = None,
        scope_user_id: str | None = None,
    ) -> list[UserEntity]:
        result = list(self._users.values())
        if username:
            # 与真实仓储语义一致：username/phone 列表筛选为包含匹配（ILIKE %v%）
            result = [u for u in result if username.lower() in (u.username or "").lower()]
        if phone:
            result = [u for u in result if phone.lower() in (u.phone or "").lower()]
        if email:
            result = [u for u in result if (u.email or "") == email]
        if is_active is not None:
            result = [u for u in result if u.is_active == is_active]
        if dept_id:
            result = [u for u in result if u.dept_id == dept_id]
        # 数据权限范围过滤（与真实仓储语义一致）
        if scope_user_id is not None:
            result = [u for u in result if u.id == scope_user_id]
        elif scope_dept_ids is not None:
            result = [] if not scope_dept_ids else [u for u in result if u.dept_id in scope_dept_ids]
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
        scope_dept_ids: list[str] | None = None,
        scope_user_id: str | None = None,
    ) -> int:
        rows = [u for u in self._users.values()]
        if username:
            # 与真实仓储语义一致：username/phone 列表筛选为包含匹配（ILIKE %v%）
            rows = [u for u in rows if username.lower() in (u.username or "").lower()]
        if phone:
            rows = [u for u in rows if phone.lower() in (u.phone or "").lower()]
        if email:
            rows = [u for u in rows if (u.email or "") == email]
        if is_active is not None:
            rows = [u for u in rows if u.is_active == is_active]
        if dept_id:
            rows = [u for u in rows if u.dept_id == dept_id]
        if scope_user_id is not None:
            rows = [u for u in rows if u.id == scope_user_id]
        elif scope_dept_ids is not None:
            rows = [] if not scope_dept_ids else [u for u in rows if u.dept_id in scope_dept_ids]
        return len(rows)

    async def batch_delete(self, user_ids: list[str]) -> int:
        removed = 0
        for uid in user_ids:
            if self._users.pop(uid, None) is not None:
                removed += 1
        return removed

    async def get_usernames_by_ids(self, user_ids: list[str]) -> dict[str, str]:
        """按 ID 批量取用户名（与真实仓储一致：查不到的 ID 不出现在结果中）。"""
        result: dict[str, str] = {}
        for uid in set(user_ids):
            user = self._users.get(uid)
            if user is not None and user.username:
                result[uid] = user.username
        return result


class InMemoryRoleRepository(RoleRepositoryInterface):
    """角色仓储的内存实现。"""

    def __init__(self, session=None, menu_entities: dict[str, MenuEntity] | None = None) -> None:
        self._roles: dict[str, RoleEntity] = {}
        self._user_roles: dict[str, list[str]] = {}
        self._role_depts: dict[str, list[str]] = {}
        self._role_menus: dict[str, list[str]] = {}
        # 可选的菜单实体注册表：get_user_all_menus 按它还原真实 menu_type；
        # 未注册的 ID 退化为 PERMISSION 类型（接口只传 ID，类型信息需外部提供）
        self._menu_entities: dict[str, MenuEntity] = dict(menu_entities or {})

    async def get_by_id(self, role_id: str) -> RoleEntity | None:
        return self._roles.get(role_id)

    async def get_by_name(self, name: str) -> RoleEntity | None:
        return next((r for r in self._roles.values() if r.name == name), None)

    async def get_by_code(self, code: str) -> RoleEntity | None:
        return next((r for r in self._roles.values() if r.code == code), None)

    async def get_all(
        self, page_num: int = 1, page_size: int = 10, role_name: str | None = None, is_active: int | None = None
    ) -> list[RoleEntity]:  # noqa: D102
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
        """先清除旧菜单再分配新的（与真实仓储语义一致）。"""
        self._role_menus[role_id] = list(menu_ids)
        return True

    async def get_role_menus(self, role_id: str) -> list:  # noqa: D102
        return list(self._role_menus.get(role_id, []))

    async def get_role_menu_ids(self, role_id: str) -> list[str]:  # noqa: D102
        return list(self._role_menus.get(role_id, []))

    async def get_user_all_menus(self, user_id: str) -> list:  # noqa: D102
        """用户所有角色关联菜单的并集（按接口契约返回 MenuEntity 列表）。

        消费方（AuthorizationService / auth_service）按实体过滤 menu_type
        并读取 name，因此返回实体——返回 ID 字符串列表会违反接口契约
        （真实仓储 join menu 表返回实体）。类型语义优先取注册表，
        未注册的 ID 退化为 PERMISSION 类型并在契约测试中显式对拍。
        """
        menu_ids: set[str] = set()
        for rid in self._user_roles.get(user_id, []):
            menu_ids.update(self._role_menus.get(rid, []))
        entities = []
        for mid in sorted(menu_ids):
            known = self._menu_entities.get(mid)
            if known is not None:
                entities.append(known)
            else:
                from src.domain.entities.menu import MenuEntity
                from src.domain.enums import MenuType

                entities.append(MenuEntity(id=mid, name=mid, menu_type=int(MenuType.PERMISSION), rank=0))
        return entities

    async def get_users_roles_batch(self, user_ids: list[str]) -> dict[str, list[RoleEntity]]:  # noqa: D102
        return {uid: await self.get_user_roles(uid) for uid in user_ids}

    async def get_roles_menu_ids_batch(self, role_ids: list[str]) -> dict[str, list[str]]:  # noqa: D102
        return {rid: list(self._role_menus.get(rid, [])) for rid in role_ids}

    async def get_roles_dept_ids_batch(self, role_ids: list[str]) -> dict[str, list[str]]:  # noqa: D102
        return {rid: list(self._role_depts.get(rid, [])) for rid in role_ids}

    # ========== 数据权限（data_scope）相关操作 ==========

    async def get_user_data_scope(self, user_id: str) -> int:  # noqa: D102
        """取用户所有启用角色中 data_scope 最小者（数值最小=范围最大）。"""
        roles = await self.get_user_roles(user_id)
        active_scopes = [r.data_scope for r in roles if r.is_active == 1 and r.data_scope is not None]
        if not active_scopes:
            # 无角色时默认仅本人可见，避免数据泄露
            return int(DataScope.SELF)
        return int(min(active_scopes))

    async def get_role_dept_ids(self, role_id: str) -> list[str]:  # noqa: D102
        return list(self._role_depts.get(role_id, []))

    async def get_user_custom_dept_ids(self, user_id: str) -> list[str]:  # noqa: D102
        """用户所有自定义数据权限角色关联的部门 ID 并集。"""
        roles = await self.get_user_roles(user_id)
        custom_role_ids = [r.id for r in roles if r.data_scope == int(DataScope.CUSTOM)]
        dept_ids: set[str] = set()
        for rid in custom_role_ids:
            dept_ids.update(self._role_depts.get(rid, []))
        return sorted(dept_ids)

    async def get_user_ids_by_role(self, role_id: str) -> list[str]:  # noqa: D102
        """持有指定角色的用户 ID（从用户-角色关联反查）。"""
        return [uid for uid, rids in self._user_roles.items() if role_id in rids]

    async def get_user_ids_by_menu(self, menu_id: str) -> list[str]:  # noqa: D102
        """经角色关联指定菜单的用户 ID（与真实仓储语义一致）。

        _role_menus 是 role_id → menu_ids 映射：遍历各角色的菜单集合，
        含目标菜单的角色，再反查持有这些角色的用户。
        """
        role_ids = [rid for rid, mids in self._role_menus.items() if menu_id in mids]
        user_ids: set[str] = set()
        for uid, rids in self._user_roles.items():
            if any(rid in rids for rid in role_ids):
                user_ids.add(uid)
        return sorted(user_ids)

    async def assign_depts_to_role(self, role_id: str, dept_ids: list[str]) -> bool:  # noqa: D102
        """先清除旧部门再分配新的。"""
        self._role_depts[role_id] = list(dept_ids)
        return True


class RecordingCacheService(UserCachePort):
    """记录调用次数的用户缓存替身，用于验证缓存失效行为。

    只实现 ``UserCachePort``：窄接口下替身不必再为无关的缓存域补 no-op 桩。
    批量失效语义同样被记录——单次调用所失效的用户数量，
    便于断言「批量操作只触发一次批量失效」而非 N 次单点失效。
    批量失效同时记录路由树失效（与真实 CacheService 的批量语义对齐：
    单次批量删除会连带 perms/info/info:full/routes 四类 Key）。
    """

    def __init__(self) -> None:
        self.invalidated_users: list[str] = []
        self.invalidate_user_info_calls: list[str] = []
        self.invalidate_user_permissions_calls: list[str] = []
        self.invalidate_user_routes_calls: list[str] = []
        self.batch_calls: list[list[str]] = []

    async def invalidate_user_info(self, user_id: str) -> bool:
        self.invalidate_user_info_calls.append(user_id)
        self.invalidated_users.append(user_id)
        return True

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        self.invalidate_user_permissions_calls.append(user_id)
        return True

    async def invalidate_user_routes(self, user_id: str) -> bool:
        self.invalidate_user_routes_calls.append(user_id)
        return True

    async def invalidate_users_batch(self, user_ids: list[str]) -> bool:
        """批量失效：一次调用处理全部用户（含路由树缓存）。"""
        self.batch_calls.append(list(user_ids))
        self.invalidated_users.extend(user_ids)
        self.invalidate_user_routes_calls.extend(user_ids)
        return True

    async def get_user_info(self, user_id: str):
        return None

    async def set_user_info(self, user_id: str, info: dict) -> bool:
        return True

    async def get_user_info_full(self, user_id: str):
        return None

    async def set_user_info_full(self, user_id: str, info: dict) -> bool:
        return True

    async def get_user_permissions(self, user_id: str):
        return None

    async def set_user_permissions(self, user_id: str, permissions: list) -> bool:
        return True

    async def get_user_routes(self, user_id: str):
        return None

    async def set_user_routes(self, user_id: str, routes: list) -> bool:
        return True


class InMemoryLogRepository(LogRepositoryInterface):
    """日志仓储的内存实现（登录日志 sys_userloginlog + 统一操作日志 sys_logs）。

    列表筛选/分页/游标语义与真实 LogRepository 对齐（见契约测试）：
    - module 为子串匹配（contains）；status/status_code 为等值；
    - 排序 created_time DESC, id DESC（None created_time 视为最小）；
    - keyset 游标 ``(created_time, id) < (before_time, before_id)`` 行比较。
    """

    def __init__(self, session=None) -> None:
        self._login_logs: list[LoginLogEntity] = []
        self._operation_logs: list[OperationLogEntity] = []
        self._session = session

    @staticmethod
    def _sort_key(entity: LoginLogEntity | OperationLogEntity) -> tuple[datetime, str]:
        """与真实仓储一致的稳定排序键（created_time DESC, id DESC）。"""
        return (entity.created_time or datetime.min, entity.id)

    # ============ 登录日志 ============

    async def get_login_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        status: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        username: str | None = None,
    ) -> tuple[list[LoginLogEntity], int]:
        rows = list(self._login_logs)
        if username:
            rows = [r for r in rows if r.username == username]
        if status is not None:
            rows = [r for r in rows if r.status == status]
        if start_time:
            rows = [r for r in rows if r.created_time is not None and r.created_time >= start_time]
        if end_time:
            rows = [r for r in rows if r.created_time is not None and r.created_time <= end_time]
        rows.sort(key=self._sort_key, reverse=True)
        offset = (page_num - 1) * page_size
        return rows[offset : offset + page_size], len(rows)

    async def create_login_log(self, log: LoginLogEntity) -> LoginLogEntity:
        self._login_logs.append(log)
        return log

    async def list_login_log_times(self, start_time: datetime, status: int | None = None) -> list[datetime]:
        return [
            r.created_time
            for r in self._login_logs
            if r.created_time is not None and r.created_time >= start_time and (status is None or r.status == status)
        ]

    async def delete_login_logs(self, log_ids: list[str]) -> int:
        removed_ids = set(log_ids)
        kept = [r for r in self._login_logs if r.id not in removed_ids]
        removed = len(self._login_logs) - len(kept)
        self._login_logs = kept
        return removed

    async def clear_login_logs(self) -> int:
        total = len(self._login_logs)
        self._login_logs.clear()
        return total

    # ============ 统一操作日志 (sys_logs) ============

    async def get_operation_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        before_time: datetime | None = None,
        before_id: str | None = None,
        total: int | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        rows = list(self._operation_logs)
        if module:
            rows = [r for r in rows if module in (r.module or "")]
        if status_code is not None:
            rows = [r for r in rows if r.status_code == status_code]
        if start_time:
            rows = [r for r in rows if r.created_time is not None and r.created_time >= start_time]
        if end_time:
            rows = [r for r in rows if r.created_time is not None and r.created_time <= end_time]
        rows.sort(key=self._sort_key, reverse=True)
        cursor_mode = before_time is not None and bool(before_id)
        if cursor_mode:
            rows = [r for r in rows if (r.created_time or datetime.min, r.id) < (before_time, before_id)]  # type: ignore[operator]
            return rows[:page_size], total if total is not None else len(rows)
        offset = (page_num - 1) * page_size
        return rows[offset : offset + page_size], total if total is not None else len(rows)

    async def create_operation_log(self, log: OperationLogEntity) -> OperationLogEntity:
        self._operation_logs.append(log)
        return log

    async def get_operation_log_detail(self, log_id: str) -> OperationLogEntity | None:
        return next((r for r in self._operation_logs if r.id == log_id), None)

    async def list_operation_log_stamps(self, start_time: datetime) -> list[tuple[datetime, str | None]]:
        return [
            (r.created_time, r.module)
            for r in self._operation_logs
            if r.created_time is not None and r.created_time >= start_time
        ]

    async def delete_operation_logs(self, log_ids: list[str]) -> int:
        removed_ids = set(log_ids)
        kept = [r for r in self._operation_logs if r.id not in removed_ids]
        removed = len(self._operation_logs) - len(kept)
        self._operation_logs = kept
        return removed

    async def clear_operation_logs(self) -> int:
        total = len(self._operation_logs)
        self._operation_logs.clear()
        return total

    # ============ 系统日志（与操作日志共享 sys_logs 表，仅查询） ============

    async def get_system_logs(
        self,
        page_num: int = 1,
        page_size: int = 10,
        module: str | None = None,
        status_code: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        before_time: datetime | None = None,
        before_id: str | None = None,
        total: int | None = None,
    ) -> tuple[list[OperationLogEntity], int]:
        """与操作日志共享同一存储（分页/游标语义一致）。"""
        return await self.get_operation_logs(
            page_num=page_num,
            page_size=page_size,
            module=module,
            status_code=status_code,
            start_time=start_time,
            end_time=end_time,
            before_time=before_time,
            before_id=before_id,
            total=total,
        )

    async def get_system_log_detail(self, log_id: str) -> OperationLogEntity | None:
        return await self.get_operation_log_detail(log_id)
