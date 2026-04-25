"""角色仓储接口的单元测试。

测试 RoleRepositoryInterface 抽象基类的方法签名和返回类型。
"""

import pytest

from src.domain.entities.menu import MenuEntity
from src.domain.entities.role import RoleEntity
from src.domain.repositories.role_repository import RoleRepositoryInterface


class ConcreteRoleRepository(RoleRepositoryInterface):
    """用于测试的 RoleRepositoryInterface 最小化具体实现。"""

    def __init__(self, session=None):
        self.session = session

    async def get_by_id(self, role_id: str) -> RoleEntity | None:
        return None

    async def get_by_name(self, name: str) -> RoleEntity | None:
        return None

    async def get_by_code(self, code: str) -> RoleEntity | None:
        return None

    async def get_all(
        self, page_num: int = 1, page_size: int = 10, role_name: str | None = None, is_active: int | None = None
    ) -> list[RoleEntity]:
        return []

    async def count(self, role_name: str | None = None, is_active: int | None = None) -> int:
        return 0

    async def create(self, role: RoleEntity) -> RoleEntity:
        return role

    async def update(self, role: RoleEntity) -> RoleEntity:
        return role

    async def delete(self, role_id: str) -> bool:
        return True

    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        return True

    async def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        return True

    async def get_user_roles(self, user_id: str) -> list[RoleEntity]:
        return []

    async def assign_roles_to_user(self, user_id: str, role_ids: list[str]) -> bool:
        return True

    async def assign_menus_to_role(self, role_id: str, menu_ids: list[str]) -> bool:
        return True

    async def get_role_menus(self, role_id: str) -> list[MenuEntity]:
        return []

    async def get_role_menu_ids(self, role_id: str) -> list[str]:
        return []

    async def get_user_all_menus(self, user_id: str) -> list[MenuEntity]:
        return []

    async def get_users_roles_batch(self, user_ids: list[str]) -> dict[str, list[RoleEntity]]:
        return {}

    async def get_roles_menu_ids_batch(self, role_ids: list[str]) -> dict[str, list[str]]:
        return {}


@pytest.mark.unit
class TestRoleRepositoryInterface:
    """RoleRepositoryInterface 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            RoleRepositoryInterface(session=None)  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        repo = ConcreteRoleRepository()
        assert repo is not None
        assert isinstance(repo, RoleRepositoryInterface)

    # ---- get_by_id ----

    @pytest.mark.asyncio
    async def test_get_by_id_accepts_str(self):
        """测试 get_by_id 接受字符串参数。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_by_id("role-1")
        assert result is None

    # ---- get_by_name ----

    @pytest.mark.asyncio
    async def test_get_by_name_accepts_str(self):
        """测试 get_by_name 接受字符串参数。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_by_name("管理员")
        assert result is None

    # ---- get_by_code ----

    @pytest.mark.asyncio
    async def test_get_by_code_accepts_str(self):
        """测试 get_by_code 接受字符串参数。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_by_code("admin")
        assert result is None

    # ---- get_all ----

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        """测试 get_all 返回列表。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_all()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_with_all_params(self):
        """测试 get_all 接受所有可选参数。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_all(page_num=1, page_size=20, role_name="admin", is_active=1)
        assert isinstance(result, list)

    # ---- count ----

    @pytest.mark.asyncio
    async def test_count_returns_int(self):
        """测试 count 返回整数。"""
        repo = ConcreteRoleRepository()
        result = await repo.count()
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_count_with_all_params(self):
        """测试 count 接受所有可选参数。"""
        repo = ConcreteRoleRepository()
        result = await repo.count(role_name="admin", is_active=1)
        assert isinstance(result, int)

    # ---- create ----

    @pytest.mark.asyncio
    async def test_create_returns_role_entity(self):
        """测试 create 返回角色实体。"""
        repo = ConcreteRoleRepository()
        entity = RoleEntity(id="role-1", name="管理员", code="admin")
        result = await repo.create(entity)
        assert isinstance(result, RoleEntity)

    # ---- update ----

    @pytest.mark.asyncio
    async def test_update_returns_role_entity(self):
        """测试 update 返回角色实体。"""
        repo = ConcreteRoleRepository()
        entity = RoleEntity(id="role-1", name="管理员", code="admin")
        result = await repo.update(entity)
        assert isinstance(result, RoleEntity)

    # ---- delete ----

    @pytest.mark.asyncio
    async def test_delete_returns_bool(self):
        """测试 delete 返回布尔值。"""
        repo = ConcreteRoleRepository()
        result = await repo.delete("role-1")
        assert isinstance(result, bool)

    # ---- assign_role_to_user ----

    @pytest.mark.asyncio
    async def test_assign_role_to_user_returns_bool(self):
        """测试 assign_role_to_user 返回布尔值。"""
        repo = ConcreteRoleRepository()
        result = await repo.assign_role_to_user("user-1", "role-1")
        assert isinstance(result, bool)

    # ---- remove_role_from_user ----

    @pytest.mark.asyncio
    async def test_remove_role_from_user_returns_bool(self):
        """测试 remove_role_from_user 返回布尔值。"""
        repo = ConcreteRoleRepository()
        result = await repo.remove_role_from_user("user-1", "role-1")
        assert isinstance(result, bool)

    # ---- get_user_roles ----

    @pytest.mark.asyncio
    async def test_get_user_roles_returns_list(self):
        """测试 get_user_roles 返回列表。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_user_roles("user-1")
        assert isinstance(result, list)

    # ---- assign_roles_to_user ----

    @pytest.mark.asyncio
    async def test_assign_roles_to_user_returns_bool(self):
        """测试 assign_roles_to_user 返回布尔值。"""
        repo = ConcreteRoleRepository()
        result = await repo.assign_roles_to_user("user-1", ["role-1", "role-2"])
        assert isinstance(result, bool)

    # ---- assign_menus_to_role ----

    @pytest.mark.asyncio
    async def test_assign_menus_to_role_returns_bool(self):
        """测试 assign_menus_to_role 返回布尔值。"""
        repo = ConcreteRoleRepository()
        result = await repo.assign_menus_to_role("role-1", ["menu-1", "menu-2"])
        assert isinstance(result, bool)

    # ---- get_role_menus ----

    @pytest.mark.asyncio
    async def test_get_role_menus_returns_list(self):
        """测试 get_role_menus 返回菜单列表。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_role_menus("role-1")
        assert isinstance(result, list)

    # ---- get_role_menu_ids ----

    @pytest.mark.asyncio
    async def test_get_role_menu_ids_returns_list(self):
        """测试 get_role_menu_ids 返回菜单 ID 列表。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_role_menu_ids("role-1")
        assert isinstance(result, list)

    # ---- get_user_all_menus ----

    @pytest.mark.asyncio
    async def test_get_user_all_menus_returns_list(self):
        """测试 get_user_all_menus 返回菜单列表。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_user_all_menus("user-1")
        assert isinstance(result, list)

    # ---- get_users_roles_batch ----

    @pytest.mark.asyncio
    async def test_get_users_roles_batch_returns_dict(self):
        """测试 get_users_roles_batch 返回字典。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_users_roles_batch(["user-1", "user-2"])
        assert isinstance(result, dict)

    # ---- get_roles_menu_ids_batch ----

    @pytest.mark.asyncio
    async def test_get_roles_menu_ids_batch_returns_dict(self):
        """测试 get_roles_menu_ids_batch 返回字典。"""
        repo = ConcreteRoleRepository()
        result = await repo.get_roles_menu_ids_batch(["role-1", "role-2"])
        assert isinstance(result, dict)
