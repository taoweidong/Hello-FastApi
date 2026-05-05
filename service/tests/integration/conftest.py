"""集成测试专用固件：真实数据库 + 先清空再种子数据。"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.database import get_db
from tests.integration.db_seed import FlowSeedData, reset_db_and_seed


@pytest_asyncio.fixture
async def flow_seed(db_session: AsyncSession) -> AsyncGenerator[FlowSeedData, None]:
    """每个用例：清空全部表 → 按顺序插入种子数据 → commit。"""
    data = await reset_db_and_seed(db_session)
    await db_session.commit()
    yield data


@pytest_asyncio.fixture
async def flow_client(db_session: AsyncSession, flow_seed: FlowSeedData, test_app) -> AsyncGenerator[AsyncClient, None]:
    """与 flow_seed 共用同一会话，接口内读写均为真实数据库操作。"""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    test_app.dependency_overrides.clear()
