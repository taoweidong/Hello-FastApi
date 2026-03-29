"""测试配置和固件。"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.database import get_db
from src.main import app

# 测试数据库 URL - 内存 SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
def event_loop():
    """为测试会话创建事件循环。"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """在每个测试前创建表，测试后删除。"""
    # 导入模型以确保它们注册到 SQLModel.metadata
    import src.infrastructure.database.models  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """提供测试数据库会话。"""
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """提供用于测试的异步 HTTP 客户端。"""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_data() -> dict:
    """提供测试用户数据（使用新字段格式）。"""
    return {
        "username": "testuser",
        "password": "TestPass123",
        "nickname": "测试用户",
        "email": "test@example.com",
        "phone": "13800138000",
        "sex": 0,
        "status": 1,
        "avatar": None,
        "deptId": None,
        "remark": "测试备注"
    }


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> AsyncGenerator[dict, None]:
    """提供认证请求头（自动创建用户并登录）。"""
    from src.application.dto.user_dto import UserCreateDTO
    from src.application.services.user_service import UserService
    from src.domain.auth.token_service import TokenService

    # 创建测试用户
    service = UserService(db_session)
    user = await service.create_user(
        UserCreateDTO(
            username="authtestuser",
            password="TestPass123",
            nickname="认证测试用户",
            email="auth@example.com",
            status=1
        )
    )
    await db_session.commit()

    # 生成访问令牌
    token = TokenService.create_access_token({"sub": user.id, "username": user.username})

    yield {"Authorization": f"Bearer {token}"}
