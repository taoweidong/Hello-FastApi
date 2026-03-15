"""API 端点的集成测试。"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.user_dto import UserCreateDTO
from src.application.services.user_service import UserService
from src.domain.auth.token_service import TokenService


@pytest.mark.integration
class TestHealthEndpoint:
    """健康检查端点测试。"""

    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.integration
class TestAuthEndpoints:
    """认证端点测试。"""

    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        # 先创建用户
        service = UserService(db_session)
        await service.create_user(
            UserCreateDTO(
                username="testuser",
                email="test@example.com",
                password="TestPass123",
            )
        )
        await db_session.commit()

        # 登录
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "TestPass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, db_session: AsyncSession):
        service = UserService(db_session)
        await service.create_user(
            UserCreateDTO(
                username="testuser2",
                email="test2@example.com",
                password="TestPass123",
            )
        )
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "testuser2", "password": "WrongPass"},
        )
        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, db_session: AsyncSession):
        # 创建用户并获取令牌
        service = UserService(db_session)
        user = await service.create_user(
            UserCreateDTO(
                username="testuser3",
                email="test3@example.com",
                password="TestPass123",
            )
        )
        await db_session.commit()

        token = TokenService.create_access_token({"sub": user.id, "username": user.username})

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser3"

    async def test_get_current_user_no_token(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)


@pytest.mark.integration
class TestUserEndpoints:
    """用户资料端点测试。"""

    async def test_get_my_profile(self, client: AsyncClient, db_session: AsyncSession):
        service = UserService(db_session)
        user = await service.create_user(
            UserCreateDTO(
                username="profileuser",
                email="profile@example.com",
                password="TestPass123",
                full_name="Profile User",
            )
        )
        await db_session.commit()

        token = TokenService.create_access_token({"sub": user.id, "username": user.username})

        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "profileuser"
        assert data["email"] == "profile@example.com"
        assert data["full_name"] == "Profile User"

    async def test_update_my_profile(self, client: AsyncClient, db_session: AsyncSession):
        service = UserService(db_session)
        user = await service.create_user(
            UserCreateDTO(
                username="updateuser",
                email="update@example.com",
                password="TestPass123",
            )
        )
        await db_session.commit()

        token = TokenService.create_access_token({"sub": user.id, "username": user.username})

        response = await client.put(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
