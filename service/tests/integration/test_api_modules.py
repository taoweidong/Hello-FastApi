"""补充集成测试 - Role、Menu、Department、IPRule 端点。"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.user_dto import UserCreateDTO
from src.application.services.user_service import UserService
from src.config.settings import get_settings
from src.domain.services.password_service import PasswordService
from src.domain.services.token_service import TokenService
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository


def _create_token_service() -> TokenService:
    settings = get_settings()
    return TokenService(
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_days=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def _create_user_service(session: AsyncSession) -> UserService:
    return UserService(
        repo=UserRepository(session),
        password_service=PasswordService(),
        role_repo=RoleRepository(session),
    )


async def _superuser_bearer(session: AsyncSession, username: str) -> str:
    """创建超级用户并返回 Bearer Token。"""
    service = _create_user_service(session)
    user = await service.create_superuser(
        UserCreateDTO(
            username=username,
            email=f"{username}@example.com",
            password="TestPass123",
            nickname=username,
        )
    )
    await session.commit()
    token = _create_token_service().create_access_token(
        {"sub": user.id, "username": user.username}
    )
    return f"Bearer {token}"


@pytest.mark.integration
class TestRoleEndpoints:
    async def test_get_role_list(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_role_list")
        response = await client.post(
            "/api/system/role",
            headers={"Authorization": auth},
            json={"pageNum": 1, "pageSize": 10},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_create_role(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_role_create")
        response = await client.post(
            "/api/system/role/create",
            headers={"Authorization": auth},
            json={
                "name": "test_role",
                "code": "test_role",
                "description": "测试角色",
                "isActive": 1,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 201
        assert result["data"]["name"] == "test_role"

    async def test_get_role_detail(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        auth = await _superuser_bearer(db_session, "su_role_detail")
        response = await client.post(
            "/api/system/role/create",
            headers={"Authorization": auth},
            json={
                "name": "detail_role",
                "code": "detail_role",
                "description": "详情测试角色",
                "isActive": 1,
            },
        )
        role_id = response.json()["data"]["id"]
        await db_session.commit()

        response = await client.get(
            f"/api/system/role/{role_id}", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert result["data"]["name"] == "detail_role"

    async def test_update_role(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_role_update")
        response = await client.post(
            "/api/system/role/create",
            headers={"Authorization": auth},
            json={
                "name": "update_role",
                "code": "update_role",
                "description": "原描述",
                "isActive": 1,
            },
        )
        role_id = response.json()["data"]["id"]
        await db_session.commit()

        response = await client.put(
            f"/api/system/role/{role_id}",
            headers={"Authorization": auth},
            json={"description": "更新后的描述"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert result["data"]["description"] == "更新后的描述"

    async def test_delete_role(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_role_delete")
        response = await client.post(
            "/api/system/role/create",
            headers={"Authorization": auth},
            json={
                "name": "delete_role",
                "code": "delete_role",
                "description": "待删除角色",
                "isActive": 1,
            },
        )
        role_id = response.json()["data"]["id"]
        await db_session.commit()

        response = await client.delete(
            f"/api/system/role/{role_id}", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        assert response.json()["code"] == 0


@pytest.mark.integration
class TestMenuEndpoints:
    async def test_get_menu_list(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_menu_list")
        response = await client.post(
            "/api/system/menu", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_get_menu_tree(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_menu_tree")
        response = await client.get(
            "/api/system/menu/tree", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_get_user_menus(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        auth = await _superuser_bearer(db_session, "su_user_menus")
        response = await client.get(
            "/api/system/menu/user-menus", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_create_menu(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_menu_create")
        response = await client.post(
            "/api/system/menu/create",
            headers={"Authorization": auth},
            json={
                "name": "test_menu",
                "path": "/test-menu",
                "component": "test/index",
                "menuType": 1,
                "rank": 100,
                "meta": {"title": "测试菜单", "icon": "ep:document", "isShowMenu": 1},
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 201
        assert result["data"]["name"] == "test_menu"


@pytest.mark.integration
class TestDepartmentEndpoints:
    async def test_get_dept_tree(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        auth = await _superuser_bearer(db_session, "su_dept_tree")
        response = await client.get(
            "/api/system/dept/tree", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_create_dept(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_dept_create")
        response = await client.post(
            "/api/system/dept/create",
            headers={"Authorization": auth},
            json={
                "name": "测试部门",
                "parentId": None,
                "sort": 100,
                "leader": "test_leader",
                "phone": "13800138000",
                "email": "dept@example.com",
                "status": 1,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 201

    async def test_update_dept(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_dept_update")
        response = await client.post(
            "/api/system/dept/create",
            headers={"Authorization": auth},
            json={
                "name": "更新部门",
                "parentId": None,
                "sort": 100,
                "status": 1,
            },
        )
        dept_id = response.json()["data"]["id"]
        await db_session.commit()

        response = await client.put(
            f"/api/system/dept/{dept_id}",
            headers={"Authorization": auth},
            json={"name": "已更新部门"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_delete_dept(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_dept_delete")
        response = await client.post(
            "/api/system/dept/create",
            headers={"Authorization": auth},
            json={
                "name": "待删除部门",
                "parentId": None,
                "sort": 100,
                "status": 1,
            },
        )
        dept_id = response.json()["data"]["id"]
        await db_session.commit()

        response = await client.delete(
            f"/api/system/dept/{dept_id}", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        assert response.json()["code"] == 0


@pytest.mark.integration
class TestIPRuleEndpoints:
    async def test_get_ip_rules(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_ip_rule_list")
        response = await client.post(
            "/api/system/ip-rule",
            headers={"Authorization": auth},
            json={"pageNum": 1, "pageSize": 10},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_create_ip_rule(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        auth = await _superuser_bearer(db_session, "su_ip_rule_create")
        response = await client.post(
            "/api/system/ip-rule/create",
            headers={"Authorization": auth},
            json={
                "ipAddress": "192.168.1.100",
                "ruleType": "blacklist",
                "reason": "测试黑名单",
                "isActive": 1,
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 201
        assert result["data"]["ipAddress"] == "192.168.1.100"

    async def test_get_ip_rule_detail(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        auth = await _superuser_bearer(db_session, "su_ip_rule_detail")
        response = await client.post(
            "/api/system/ip-rule/create",
            headers={"Authorization": auth},
            json={
                "ipAddress": "192.168.1.101",
                "ruleType": "whitelist",
                "reason": "测试白名单",
                "isActive": 1,
            },
        )
        rule_id = response.json()["data"]["id"]
        await db_session.commit()

        response = await client.get(
            f"/api/system/ip-rule/{rule_id}", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert result["data"]["ipAddress"] == "192.168.1.101"

    async def test_update_ip_rule(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        auth = await _superuser_bearer(db_session, "su_ip_rule_update")
        response = await client.post(
            "/api/system/ip-rule/create",
            headers={"Authorization": auth},
            json={
                "ipAddress": "192.168.1.102",
                "ruleType": "blacklist",
                "reason": "原原因",
                "isActive": 1,
            },
        )
        rule_id = response.json()["data"]["id"]
        await db_session.commit()

        response = await client.put(
            f"/api/system/ip-rule/{rule_id}",
            headers={"Authorization": auth},
            json={"reason": "更新后的原因"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_delete_ip_rule(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        auth = await _superuser_bearer(db_session, "su_ip_rule_delete")
        response = await client.post(
            "/api/system/ip-rule/create",
            headers={"Authorization": auth},
            json={
                "ipAddress": "192.168.1.103",
                "ruleType": "blacklist",
                "reason": "待删除",
                "isActive": 1,
            },
        )
        rule_id = response.json()["data"]["id"]
        await db_session.commit()

        response = await client.delete(
            f"/api/system/ip-rule/{rule_id}", headers={"Authorization": auth}
        )
        assert response.status_code == 200
        assert response.json()["code"] == 0

    async def test_batch_delete_ip_rules(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        auth = await _superuser_bearer(db_session, "su_ip_rule_batch")
        ids = []
        for i in range(3):
            response = await client.post(
                "/api/system/ip-rule/create",
                headers={"Authorization": auth},
                json={
                    "ipAddress": f"192.168.1.{200 + i}",
                    "ruleType": "blacklist",
                    "isActive": 1,
                },
            )
            ids.append(response.json()["data"]["id"])
        await db_session.commit()

        response = await client.post(
            "/api/system/ip-rule/batch-delete",
            headers={"Authorization": auth},
            json={"ids": ids},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert result["data"]["deleted"] == 3
