"""领域实体的单元测试。"""

from datetime import datetime, timedelta

import pytest

from src.domain.entities.department import DepartmentEntity
from src.domain.entities.dictionary import DictionaryEntity
from src.domain.entities.ip_rule import IPRuleEntity
from src.domain.entities.log import LoginLogEntity, OperationLogEntity, SystemLogEntity
from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.entities.role import RoleEntity
from src.domain.entities.system_config import SystemConfigEntity
from src.domain.entities.user import UserEntity


@pytest.mark.unit
class TestUserEntity:
    """UserEntity 测试类。"""

    def test_properties_superuser(self):
        """测试超级用户属性。"""
        user = UserEntity(id="1", username="admin", password="hash", is_superuser=1)
        assert user.is_superuser_user is True
        assert user.is_active_user is True

    def test_properties_normal_user(self):
        """测试普通用户属性。"""
        user = UserEntity(id="1", username="user", password="hash", is_superuser=0, is_active=0)
        assert user.is_superuser_user is False
        assert user.is_active_user is False

    def test_activate(self):
        """测试启用用户。"""
        user = UserEntity(id="1", username="user", password="hash", is_active=0)
        user.activate()
        assert user.is_active == 1
        assert user.is_active_user is True

    def test_deactivate(self):
        """测试禁用用户。"""
        user = UserEntity(id="1", username="user", password="hash", is_active=1)
        user.deactivate()
        assert user.is_active == 0
        assert user.is_active_user is False

    def test_change_password(self):
        """测试修改密码。"""
        user = UserEntity(id="1", username="user", password="old_hash")
        user.change_password("new_hash")
        assert user.password == "new_hash"

    def test_update_profile_partial(self):
        """测试部分更新用户档案。"""
        user = UserEntity(id="1", username="user", password="hash", email="old@test.com", nickname="old")
        user.update_profile(email="new@test.com")
        assert user.email == "new@test.com"
        assert user.nickname == "old"

    def test_update_profile_all_fields(self):
        """测试更新所有用户档案字段。"""
        user = UserEntity(id="1", username="user", password="hash")
        user.update_profile(email="e@t.com", nickname="nick", first_name="F", last_name="L", phone="123", gender=1, avatar="a.png", is_active=0, is_staff=1, mode_type=1, dept_id="d1", description="desc")
        assert user.email == "e@t.com"
        assert user.nickname == "nick"
        assert user.first_name == "F"
        assert user.last_name == "L"
        assert user.phone == "123"
        assert user.gender == 1
        assert user.avatar == "a.png"
        assert user.is_active == 0
        assert user.is_staff == 1
        assert user.mode_type == 1
        assert user.dept_id == "d1"
        assert user.description == "desc"

    def test_update_profile_none_unchanged(self):
        """测试 update_profile 传入 None 不修改字段。"""
        user = UserEntity(id="1", username="user", password="hash", email="keep@me.com", nickname="keep")
        user.update_profile(email=None, nickname=None)
        assert user.email == "keep@me.com"
        assert user.nickname == "keep"

    def test_create_new(self):
        """测试工厂方法创建新用户。"""
        user = UserEntity.create_new(username="testuser", hashed_password="hashed", email="t@t.com", nickname="昵称")
        assert len(user.id) == 32
        assert user.username == "testuser"
        assert user.password == "hashed"
        assert user.email == "t@t.com"
        assert user.nickname == "昵称"
        assert user.is_active == 1
        assert user.is_superuser == 0

    def test_create_superuser_entity(self):
        """测试工厂方法创建超级用户。"""
        user = UserEntity.create_superuser_entity(username="admin", hashed_password="hashed")
        assert user.is_superuser == 1
        assert user.is_staff == 1
        assert user.is_active == 1


@pytest.mark.unit
class TestRoleEntity:
    """RoleEntity 测试类。"""

    def test_is_active_role(self):
        """测试角色启用属性。"""
        role = RoleEntity(id="1", name="admin", code="admin", is_active=1)
        assert role.is_active_role is True
        role.is_active = 0
        assert role.is_active_role is False

    def test_activate_deactivate(self):
        """测试角色启用/禁用。"""
        role = RoleEntity(id="1", name="admin", code="admin", is_active=0)
        role.activate()
        assert role.is_active == 1
        role.deactivate()
        assert role.is_active == 0

    def test_update_info(self):
        """测试更新角色信息。"""
        role = RoleEntity(id="1", name="old", code="old_code")
        role.update_info(name="new", code="new_code", description="desc", is_active=0)
        assert role.name == "new"
        assert role.code == "new_code"
        assert role.description == "desc"
        assert role.is_active == 0

    def test_update_info_partial(self):
        """测试部分更新角色信息。"""
        role = RoleEntity(id="1", name="keep", code="keep")
        role.update_info(name="changed")
        assert role.name == "changed"
        assert role.code == "keep"

    def test_create_new(self):
        """测试工厂方法创建角色。"""
        role = RoleEntity.create_new(name="test", code="test", description="测试角色")
        assert len(role.id) == 32
        assert role.name == "test"
        assert role.code == "test"
        assert role.is_active == 1


@pytest.mark.unit
class TestMenuEntity:
    """MenuEntity 测试类。"""

    def test_type_properties(self):
        """测试菜单类型属性。"""
        menu = MenuEntity(id="1", menu_type=0)
        assert menu.is_directory is True
        assert menu.is_menu_page is False
        assert menu.is_permission is False

        menu.menu_type = 1
        assert menu.is_menu_page is True

        menu.menu_type = 2
        assert menu.is_permission is True

    def test_is_active_menu(self):
        """测试菜单启用属性。"""
        menu = MenuEntity(id="1", is_active=1)
        assert menu.is_active_menu is True
        menu.is_active = 0
        assert menu.is_active_menu is False

    def test_circular_reference(self):
        """测试循环引用检查。"""
        menu = MenuEntity(id="menu-1")
        assert menu.is_circular_reference("menu-1") is True
        assert menu.is_circular_reference("menu-2") is False
        assert menu.is_circular_reference(None) is False

    def test_update_info(self):
        """测试更新菜单信息。"""
        menu = MenuEntity(id="1", name="old", path="/old")
        menu.update_info(name="new", path="/new", menu_type=1, component="comp", rank=5, is_active=0, method="POST", parent_id="p1", description="desc")
        assert menu.name == "new"
        assert menu.path == "/new"
        assert menu.menu_type == 1
        assert menu.component == "comp"
        assert menu.rank == 5
        assert menu.is_active == 0
        assert menu.method == "POST"
        assert menu.parent_id == "p1"
        assert menu.description == "desc"

    def test_create_new(self):
        """测试工厂方法创建菜单。"""
        menu = MenuEntity.create_new(name="test_menu", menu_type=1, path="/test", component="TestComp", rank=3)
        assert len(menu.id) == 32
        assert menu.name == "test_menu"
        assert menu.menu_type == 1
        assert menu.is_active == 1


@pytest.mark.unit
class TestMenuMetaEntity:
    """MenuMetaEntity 测试类。"""

    def test_update_info(self):
        """测试更新菜单元数据。"""
        meta = MenuMetaEntity(id="1", title="旧标题")
        meta.update_info(title="新标题", icon="home", r_svg_name="ri-home", is_show_menu=0, is_show_parent=1, is_keepalive=1, frame_url="http://x.com", frame_loading=0, transition_enter="fade", transition_leave="slide", is_hidden_tag=1, fixed_tag=1, dynamic_level=3, description="desc")
        assert meta.title == "新标题"
        assert meta.icon == "home"
        assert meta.r_svg_name == "ri-home"
        assert meta.is_show_menu == 0
        assert meta.is_show_parent == 1
        assert meta.is_keepalive == 1
        assert meta.frame_url == "http://x.com"
        assert meta.frame_loading == 0
        assert meta.transition_enter == "fade"
        assert meta.transition_leave == "slide"
        assert meta.is_hidden_tag == 1
        assert meta.fixed_tag == 1
        assert meta.dynamic_level == 3
        assert meta.description == "desc"

    def test_update_info_partial(self):
        """测试部分更新菜单元数据。"""
        meta = MenuMetaEntity(id="1", title="keep", icon="old")
        meta.update_info(icon="new")
        assert meta.title == "keep"
        assert meta.icon == "new"

    def test_create_new(self):
        """测试工厂方法创建菜单元数据。"""
        meta = MenuMetaEntity.create_new(title="测试")
        assert len(meta.id) == 32
        assert meta.title == "测试"
        assert meta.is_show_menu == 1


@pytest.mark.unit
class TestDepartmentEntity:
    """DepartmentEntity 测试类。"""

    def test_is_active_dept(self):
        """测试部门启用属性。"""
        dept = DepartmentEntity(id="1", is_active=1)
        assert dept.is_active_dept is True
        dept.is_active = 0
        assert dept.is_active_dept is False

    def test_circular_reference(self):
        """测试循环引用检查。"""
        dept = DepartmentEntity(id="dept-1")
        assert dept.is_circular_reference("dept-1") is True
        assert dept.is_circular_reference("dept-2") is False
        assert dept.is_circular_reference(None) is False

    def test_update_info(self):
        """测试更新部门信息。"""
        dept = DepartmentEntity(id="1", name="old", code="old")
        dept.update_info(name="new", code="new", mode_type=1, rank=5, auto_bind=1, parent_id="p1", description="desc")
        assert dept.name == "new"
        assert dept.code == "new"
        assert dept.mode_type == 1
        assert dept.rank == 5
        assert dept.auto_bind == 1
        assert dept.parent_id == "p1"
        assert dept.description == "desc"

    def test_create_new(self):
        """测试工厂方法创建部门。"""
        dept = DepartmentEntity.create_new(name="技术部", code="tech", parent_id="p1")
        assert len(dept.id) == 32
        assert dept.name == "技术部"
        assert dept.code == "tech"
        assert dept.parent_id == "p1"
        assert dept.is_active == 1


@pytest.mark.unit
class TestDictionaryEntity:
    """DictionaryEntity 测试类。"""

    def test_circular_reference(self):
        """测试循环引用检查。"""
        d = DictionaryEntity(id="dict-1")
        assert d.is_circular_reference("dict-1") is True
        assert d.is_circular_reference("dict-2") is False
        assert d.is_circular_reference(None) is False

    def test_update_info(self):
        """测试更新字典信息。"""
        d = DictionaryEntity(id="1", name="old", label="旧标签", value="v1")
        d.update_info(name="new", label="新标签", value="v2", sort=5, is_active=0, parent_id="p1", description="desc")
        assert d.name == "new"
        assert d.label == "新标签"
        assert d.value == "v2"
        assert d.sort == 5
        assert d.is_active == 0
        assert d.parent_id == "p1"
        assert d.description == "desc"

    def test_create_new(self):
        """测试工厂方法创建字典。"""
        d = DictionaryEntity.create_new(name="status", label="状态", value="1", sort=1, parent_id="p1")
        assert len(d.id) == 32
        assert d.name == "status"
        assert d.is_active == 1


@pytest.mark.unit
class TestIPRuleEntity:
    """IPRuleEntity 测试类。"""

    def test_rule_type_properties(self):
        """测试规则类型属性。"""
        rule = IPRuleEntity(id="1", rule_type="whitelist")
        assert rule.is_whitelist is True
        assert rule.is_blacklist is False

        rule.rule_type = "blacklist"
        assert rule.is_whitelist is False
        assert rule.is_blacklist is True

    def test_is_expired_no_expiry(self):
        """测试无过期时间时未过期。"""
        rule = IPRuleEntity(id="1", expires_at=None)
        assert rule.is_expired is False

    def test_is_expired_past(self):
        """测试已过期。"""
        rule = IPRuleEntity(id="1", expires_at=datetime.now() - timedelta(hours=1))
        assert rule.is_expired is True

    def test_is_expired_future(self):
        """测试未过期。"""
        rule = IPRuleEntity(id="1", expires_at=datetime.now() + timedelta(hours=1))
        assert rule.is_expired is False

    def test_is_effective(self):
        """测试规则生效判断。"""
        # 活跃且未过期
        rule = IPRuleEntity(id="1", is_active=1, expires_at=datetime.now() + timedelta(hours=1))
        assert rule.is_effective is True

        # 禁用
        rule.is_active = 0
        assert rule.is_effective is False

        # 已过期
        rule.is_active = 1
        rule.expires_at = datetime.now() - timedelta(hours=1)
        assert rule.is_effective is False

    def test_update_info(self):
        """测试更新IP规则信息。"""
        rule = IPRuleEntity(id="1", ip_address="1.1.1.1", rule_type="blacklist")
        new_expires = datetime.now() + timedelta(days=1)
        rule.update_info(ip_address="2.2.2.2", rule_type="whitelist", reason="测试", is_active=0, expires_at=new_expires, description="desc")
        assert rule.ip_address == "2.2.2.2"
        assert rule.rule_type == "whitelist"
        assert rule.reason == "测试"
        assert rule.is_active == 0
        assert rule.expires_at == new_expires
        assert rule.description == "desc"

    def test_create_new(self):
        """测试工厂方法创建IP规则。"""
        rule = IPRuleEntity.create_new(ip_address="1.1.1.1", rule_type="blacklist", reason="测试")
        assert len(rule.id) == 32
        assert rule.ip_address == "1.1.1.1"
        assert rule.rule_type == "blacklist"
        assert rule.is_active == 1


@pytest.mark.unit
class TestSystemConfigEntity:
    """SystemConfigEntity 测试类。"""

    def test_update_info(self):
        """测试更新系统配置信息。"""
        config = SystemConfigEntity(id="1", key="old_key", value="old_val")
        config.update_info(value="new_val", is_active=0, access=1, key="new_key", inherit=1, description="desc")
        assert config.value == "new_val"
        assert config.is_active == 0
        assert config.access == 1
        assert config.key == "new_key"
        assert config.inherit == 1
        assert config.description == "desc"

    def test_create_new(self):
        """测试工厂方法创建系统配置。"""
        config = SystemConfigEntity.create_new(key="site_name", value="MyApp", description="站点名称")
        assert len(config.id) == 32
        assert config.key == "site_name"
        assert config.value == "MyApp"


@pytest.mark.unit
class TestLoginLogEntity:
    """LoginLogEntity 测试类。"""

    def test_is_success(self):
        """测试登录成功判断。"""
        log = LoginLogEntity(id="1", status=1)
        assert log.is_success is True
        log.status = 0
        assert log.is_success is False

    def test_create_new(self):
        """测试工厂方法创建登录日志。"""
        log = LoginLogEntity.create_new(status=1, ipaddress="127.0.0.1", browser="Chrome", system="Windows", agent="Mozilla/5.0", login_type=0, description="测试")
        assert len(log.id) == 32
        assert log.status == 1
        assert log.ipaddress == "127.0.0.1"


@pytest.mark.unit
class TestOperationLogEntity:
    """OperationLogEntity 测试类。"""

    def test_create_new(self):
        """测试工厂方法创建操作日志。"""
        log = OperationLogEntity.create_new(module="用户管理", path="/api/users", method="POST", ipaddress="127.0.0.1", browser="Chrome", system="Windows", response_code=200, response_result="success", status_code=0, description="测试")
        assert len(log.id) == 32
        assert log.module == "用户管理"
        assert log.path == "/api/users"
        assert log.method == "POST"

    def test_system_log_alias(self):
        """测试 SystemLogEntity 是 OperationLogEntity 的别名。"""
        assert SystemLogEntity is OperationLogEntity
