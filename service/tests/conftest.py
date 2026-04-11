"""测试配置和固件。"""

import os

os.environ.setdefault("APP_ENV", "testing")

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.lifespan import empty_lifespan
from src.infrastructure.database import get_db
from src.main import create_app

# 测试数据库 URL - 使用共享内存 SQLite (支持多连接共享同一数据库)
TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


@pytest.fixture(scope="session")
def test_app():
    """测试专用应用实例（不执行生产 lifespan 中的数据库初始化）。"""
    return create_app(lifespan_override=empty_lifespan)


@pytest.fixture(scope="session")
def event_loop():
    """为测试会话创建事件循环。"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """在每个测试前创建表，测试后删除。"""
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
async def client(db_session: AsyncSession, test_app) -> AsyncGenerator[AsyncClient, None]:
    """提供用于测试的异步 HTTP 客户端。"""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_data() -> dict:
    """提供测试用户数据（使用新字段格式）。"""
    return {"username": "testuser", "password": "TestPass123", "nickname": "测试用户", "email": "test@example.com", "phone": "13800138000", "sex": 0, "status": 1, "avatar": None, "deptId": None, "remark": "测试备注"}


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> AsyncGenerator[dict, None]:
    """提供认证请求头（超级管理员，便于通过 RBAC 依赖）。"""
    from src.application.dto.user_dto import UserCreateDTO
    from src.application.services.user_service import UserService
    from src.config.settings import get_settings
    from src.domain.services.password_service import PasswordService
    from src.domain.services.token_service import TokenService
    from src.infrastructure.repositories.role_repository import RoleRepository
    from src.infrastructure.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    role_repo = RoleRepository(db_session)
    password_service = PasswordService()
    service = UserService(session=db_session, repo=user_repo, password_service=password_service, role_repo=role_repo)
    user = await service.create_superuser(UserCreateDTO(username="authtestuser", password="TestPass123", nickname="认证测试用户", email="auth@example.com", status=1))
    await db_session.commit()

    settings = get_settings()
    token_service = TokenService(secret_key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM, access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES, refresh_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token = token_service.create_access_token({"sub": user.id, "username": user.username})

    yield {"Authorization": f"Bearer {token}"}
