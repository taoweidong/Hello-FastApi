"""API 端点的集成测试。"""

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
    return TokenService(secret_key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM, access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES, refresh_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


def _create_user_service(session: AsyncSession) -> UserService:
    return UserService(repo=UserRepository(session), password_service=PasswordService(), role_repo=RoleRepository(session))


async def _superuser_bearer(session: AsyncSession, username: str) -> str:
    """创建超级用户并返回 Bearer Token（通过 RBAC 依赖）。"""
    service = _create_user_service(session)
    user = await service.create_superuser(UserCreateDTO(username=username, email=f"{username}@example.com", password="TestPass123", nickname=username, isActive=True))
    await session.commit()
    token = _create_token_service().create_access_token({"sub": user.id, "username": user.username})
    return f"Bearer {token}"


@pytest.mark.integration
class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.integration
class TestAuthEndpoints:
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        service = _create_user_service(db_session)
        await service.create_user(UserCreateDTO(username="testuser", email="test@example.com", password="TestPass123", nickname="测试用户", isActive=True))
        await db_session.commit()

        response = await client.post("/api/system/login", json={"username": "testuser", "password": "TestPass123"})
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        data = result["data"]
        assert "accessToken" in data
        assert "refreshToken" in data
        assert "expires" in data

    async def test_login_wrong_password(self, client: AsyncClient, db_session: AsyncSession):
        service = _create_user_service(db_session)
        await service.create_user(UserCreateDTO(username="testuser2", email="test2@example.com", password="TestPass123", nickname="测试用户2", isActive=True))
        await db_session.commit()

        response = await client.post("/api/system/login", json={"username": "testuser2", "password": "WrongPass"})
        assert response.status_code == 401
        result = response.json()
        assert result["code"] == 401
        assert "message" in result

    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/api/system/register", json={"username": "newuser", "password": "TestPass123", "nickname": "新用户", "email": "new@example.com"})
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        data = result["data"]
        assert data["username"] == "newuser"
        assert data["nickname"] == "新用户"

    async def test_logout(self, client: AsyncClient, db_session: AsyncSession):
        service = _create_user_service(db_session)
        user = await service.create_user(UserCreateDTO(username="logoutuser", email="logout@example.com", password="TestPass123", isActive=True))
        await db_session.commit()

        token = _create_token_service().create_access_token({"sub": user.id, "username": user.username})

        response = await client.post("/api/system/logout", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0

    async def test_refresh_token(self, client: AsyncClient, db_session: AsyncSession):
        service = _create_user_service(db_session)
        await service.create_user(UserCreateDTO(username="refreshuser", email="refresh@example.com", password="TestPass123", isActive=True))
        await db_session.commit()

        login_response = await client.post("/api/system/login", json={"username": "refreshuser", "password": "TestPass123"})
        login_data = login_response.json()["data"]
        refresh_token = login_data["refreshToken"]

        response = await client.post("/api/system/refresh-token", json={"refreshToken": refresh_token})
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        data = result["data"]
        assert "accessToken" in data
        assert "refreshToken" in data

    async def test_get_current_user_info(self, client: AsyncClient, db_session: AsyncSession):
        service = _create_user_service(db_session)
        user = await service.create_user(UserCreateDTO(username="testuser3", email="test3@example.com", password="TestPass123", nickname="测试用户3", isActive=True))
        await db_session.commit()

        token = _create_token_service().create_access_token({"sub": user.id, "username": user.username})

        response = await client.get("/api/system/user/info", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        data = result["data"]
        assert data["username"] == "testuser3"
        assert data["nickname"] == "测试用户3"

    async def test_get_current_user_no_token(self, client: AsyncClient):
        response = await client.get("/api/system/user/info")
        assert response.status_code in (401, 403)


@pytest.mark.integration
class TestUserManagementEndpoints:
    async def test_get_user_list(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_list_user")
        service = _create_user_service(db_session)
        await service.create_user(UserCreateDTO(username="listuser", email="list@example.com", password="TestPass123", nickname="列表用户", isActive=True))
        await db_session.commit()

        response = await client.post("/api/system/user", headers={"Authorization": auth}, json={"pageNum": 1, "pageSize": 10})
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert "data" in result

    async def test_create_user(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_create_user")
        response = await client.post("/api/system/user/create", headers={"Authorization": auth}, json={"username": "createduser", "password": "TestPass123", "nickname": "创建的用户", "email": "created@example.com", "phone": "13800138001", "gender": 0, "isActive": True})
        assert response.status_code == 201
        result = response.json()
        assert result["code"] == 201
        data = result["data"]
        assert data["username"] == "createduser"
        assert data["nickname"] == "创建的用户"

    async def test_get_user_detail(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_detail_user")
        service = _create_user_service(db_session)
        user = await service.create_user(UserCreateDTO(username="detailuser", email="detail@example.com", password="TestPass123", nickname="详情用户", isActive=True))
        await db_session.commit()

        response = await client.get(f"/api/system/user/{user.id}", headers={"Authorization": auth})
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert result["data"]["username"] == "detailuser"

    async def test_update_user(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_update_user")
        service = _create_user_service(db_session)
        user = await service.create_user(UserCreateDTO(username="updateuser", email="update@example.com", password="TestPass123", nickname="原昵称", isActive=True))
        await db_session.commit()

        response = await client.put(f"/api/system/user/{user.id}", headers={"Authorization": auth}, json={"nickname": "更新后的昵称", "description": "更新备注"})
        assert response.status_code == 200
        result = response.json()
        assert result["code"] == 0
        assert result["data"]["nickname"] == "更新后的昵称"

    async def test_delete_user(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_delete_user")
        service = _create_user_service(db_session)
        user = await service.create_user(UserCreateDTO(username="deleteuser", email="delete@example.com", password="TestPass123", nickname="待删除用户", isActive=True))
        await db_session.commit()

        response = await client.delete(f"/api/system/user/{user.id}", headers={"Authorization": auth})
        assert response.status_code == 200
        assert response.json()["code"] == 0

    async def test_change_password(self, client: AsyncClient, db_session: AsyncSession):
        service = _create_user_service(db_session)
        user = await service.create_user(UserCreateDTO(username="passworduser", email="password@example.com", password="OldPass123", nickname="密码用户", isActive=True))
        await db_session.commit()

        token = _create_token_service().create_access_token({"sub": user.id, "username": user.username})

        response = await client.post("/api/system/user/change-password", headers={"Authorization": f"Bearer {token}"}, json={"oldPassword": "OldPass123", "newPassword": "NewPass123"})
        assert response.status_code == 200
        assert response.json()["code"] == 0

    async def test_update_user_status(self, client: AsyncClient, db_session: AsyncSession):
        auth = await _superuser_bearer(db_session, "su_status_user")
        service = _create_user_service(db_session)
        user = await service.create_user(UserCreateDTO(username="statususer", email="status@example.com", password="TestPass123", nickname="状态用户", isActive=True))
        await db_session.commit()

        response = await client.put(f"/api/system/user/{user.id}/status", headers={"Authorization": auth}, json={"isActive": False})
        assert response.status_code == 200
        assert response.json()["code"] == 0
