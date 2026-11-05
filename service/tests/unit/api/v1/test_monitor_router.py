"""系统监控路由模块单元测试。"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from src.infrastructure.http.exception_handler_registry import register_exception_handlers


class _FakeCache:
    """缓存服务替身：预置在线会话列表并记录删除/拉黑调用。"""

    def __init__(self, sessions: list[dict] | None = None):
        self._sessions = list(sessions or [])
        self.deleted: list[str] = []
        self.blacklisted: list[str] = []

    async def get_online_users(self) -> list[dict]:
        return [dict(item) for item in self._sessions]

    async def get_online_user(self, session_key: str) -> dict | None:
        for item in self._sessions:
            if item.get("id") == session_key:
                return dict(item)
        return None

    async def delete_online_user(self, session_key: str) -> bool:
        self.deleted.append(session_key)
        return True

    async def blacklist_token_hash(self, token_hash: str, expires_at) -> bool:
        self.blacklisted.append(token_hash)
        return True


def _make_session(session_id: str, username: str, login_time: str) -> dict:
    """构造一条在线会话记录（含 id=session_key）。"""
    return {
        "id": session_id,
        "userId": f"u-{session_id}",
        "username": username,
        "ip": "127.0.0.1",
        "system": "Windows",
        "browser": "Chrome",
        "loginTime": login_time,
        "expiresAt": "2099-01-01T00:00:00+00:00",
    }


@pytest.mark.unit
class TestMonitorRouter:
    """系统监控路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.monitor_router import MonitorRouter

        _app.include_router(MonitorRouter().router, prefix="/api/system")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_user_entity(self):
        return UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)

    @pytest.fixture
    def client(self, app, mock_user_entity):
        from src.api.dependencies import get_current_active_user
        from src.api.dependencies.monitor_service import get_monitor_service, get_redis_or_none
        from src.application.services.monitor_service import MonitorService

        app.dependency_overrides[get_current_active_user] = lambda: mock_user_entity
        # 禁用 Redis 依赖，缓存监控走降级分支，避免单测依赖真实 Redis
        app.dependency_overrides[get_redis_or_none] = lambda: None
        # 在线用户接口注入内存替身缓存
        fake_cache = _FakeCache(
            sessions=[
                _make_session("hash1", "admin", "2026-03-29T10:00:00"),
                _make_session("hash2", "common", "2026-03-29T09:30:00"),
            ]
        )
        self._fake_cache = fake_cache
        app.dependency_overrides[get_monitor_service] = lambda: MonitorService(
            session_store=fake_cache, token_revocation=fake_cache
        )
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_online_logs(self, client):
        resp = client.post("/api/system/online-logs", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["list"]) == 2
        assert data["data"]["total"] == 2
        first = data["data"]["list"][0]
        for key in ("id", "username", "ip", "system", "browser", "loginTime"):
            assert key in first

    def test_get_online_logs_filter(self, client):
        resp = client.post("/api/system/online-logs", json={"username": "admin"}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["list"]) == 1
        assert data["data"]["list"][0]["username"] == "admin"

    def test_force_offline(self, client):
        resp = client.post("/api/system/online-logs/force-offline", json={"id": "hash1"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "强制下线成功"
        assert self._fake_cache.deleted == ["hash1"]
        assert self._fake_cache.blacklisted == ["hash1"]

    def test_force_offline_without_cache_degraded(self, app, mock_user_entity):
        """缓存服务未注入时强制下线走全局异常体系返回 400（HTTP 语义正确）。"""
        from src.api.dependencies import get_current_active_user
        from src.api.dependencies.monitor_service import get_monitor_service
        from src.application.services.monitor_service import MonitorService

        app.dependency_overrides[get_current_active_user] = lambda: mock_user_entity
        app.dependency_overrides[get_monitor_service] = lambda: MonitorService()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/system/online-logs/force-offline", json={"id": "hash1"}, headers=self.auth)
        assert resp.status_code == 400
        assert "缓存服务不可用" in resp.json()["message"]

    def test_get_map_info(self, client):
        resp = client.get("/api/system/get-map-info", headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) == 50

    def test_get_card_list(self, client):
        resp = client.post("/api/system/get-card-list", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["list"]) == 48

    def test_get_server_info(self, client):
        resp = client.get("/api/system/server-info", headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        payload = data["data"]
        for key in ("cpu", "memory", "disk", "system", "process"):
            assert key in payload
        assert payload["cpu"]["coreCount"] >= 1

    def test_get_cache_info_degraded(self, client):
        """Redis 依赖被覆写为 None 时返回降级结构。"""
        resp = client.get("/api/system/cache-info", headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["connected"] is False
        assert data["data"]["message"]


@pytest.mark.unit
class TestCacheAdminRouter:
    """缓存清单与清理接口：权限（仅管理员）与降级语义。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.monitor_router import MonitorRouter

        _app.include_router(MonitorRouter().router, prefix="/api/system")
        return _app

    @pytest.fixture
    def mock_admin_service(self):
        from unittest.mock import AsyncMock

        from src.application.dto.monitor_dto import CacheGroupDTO

        svc = AsyncMock()
        # 服务层契约：返回 CacheGroupDTO 列表（路由层负责 model_dump）
        svc.get_cache_groups.return_value = [
            CacheGroupDTO(key="user_info", name="用户信息缓存", prefix="user:info:", count=3, clearable=True),
            CacheGroupDTO(
                key="token_blacklist", name="令牌黑名单", prefix="token:blacklist:", count=1, clearable=False
            ),
        ]
        svc.clear_cache_group.return_value = 3
        svc.clear_all_cache.return_value = 7
        return svc

    def _build_client(self, app, service, user_entity):
        from src.api.dependencies import get_current_active_user
        from src.api.dependencies.monitor_service import get_monitor_service

        app.dependency_overrides[get_current_active_user] = lambda: user_entity
        app.dependency_overrides[get_monitor_service] = lambda: service
        return TestClient(app, raise_server_exceptions=False)

    def test_cache_groups_requires_admin(self, app, mock_admin_service):
        """cache-groups 属 monitor:view，但清理按钮的权限码由前端 v-auth 控制；
        该接口本身普通登录用户（monitor:view 权限）即可访问。"""
        # 管理员可访问
        client = self._build_client(
            app, mock_admin_service, UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)
        )
        resp = client.get("/api/system/cache-groups", headers={"Authorization": "Bearer t"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert {g["key"] for g in data} == {"user_info", "token_blacklist"}

    def test_cache_clear_requires_superuser(self, app, mock_admin_service):
        """非管理员调用清理接口必须 403（require_superuser）。"""
        normal_user = UserEntity(id="2", username="user", password="", is_superuser=UserRole.USER)
        client = self._build_client(app, mock_admin_service, normal_user)
        resp = client.post(
            "/api/system/cache-clear", json={"group": "user_info"}, headers={"Authorization": "Bearer t"}
        )
        assert resp.status_code == 403
        resp = client.post("/api/system/cache-clear-all", headers={"Authorization": "Bearer t"})
        assert resp.status_code == 403
        mock_admin_service.clear_cache_group.assert_not_awaited()

    def test_cache_clear_by_superuser(self, app, mock_admin_service):
        client = self._build_client(
            app, mock_admin_service, UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)
        )
        resp = client.post(
            "/api/system/cache-clear", json={"group": "user_info"}, headers={"Authorization": "Bearer t"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == {"group": "user_info", "deleted": 3}

        resp = client.post("/api/system/cache-clear-all", headers={"Authorization": "Bearer t"})
        assert resp.status_code == 200
        assert resp.json()["data"] == {"group": "all", "deleted": 7}

    def test_cache_clear_unknown_group_400(self, app):
        """未知分组：端口抛 ValueError，服务层转 BusinessError → 400。

        必须注入真实 MonitorService（错误映射发生在服务层），
        仅 mock CacheAdminPort。
        """
        from unittest.mock import AsyncMock

        from src.application.services.monitor_service import MonitorService

        mock_admin = AsyncMock()
        mock_admin.clear_cache_group.side_effect = ValueError("未知的缓存分组: nope")
        svc = MonitorService(cache_admin=mock_admin)
        client = self._build_client(
            app, svc, UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)
        )
        resp = client.post("/api/system/cache-clear", json={"group": "nope"}, headers={"Authorization": "Bearer t"})
        assert resp.status_code == 400

    def test_cache_clear_unavailable_400(self, app):
        """Redis 不可用时服务层抛 BusinessError → 400（与强制下线语义一致）。"""
        from unittest.mock import AsyncMock

        from src.application.services.monitor_service import MonitorService

        mock_admin = AsyncMock()
        # Redis 不可用：端口返回 None（而非抛错），服务层转 BusinessError
        mock_admin.clear_all_business_cache.return_value = None
        svc = MonitorService(cache_admin=mock_admin)
        client = self._build_client(
            app, svc, UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)
        )
        resp = client.post("/api/system/cache-clear-all", headers={"Authorization": "Bearer t"})
        assert resp.status_code == 400
        assert "缓存服务不可用" in resp.json()["message"]
