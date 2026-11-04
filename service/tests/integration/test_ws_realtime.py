"""实时消息 WebSocket 路由集成测试。

覆盖：有效 token 可连接并收到 connected + 心跳 pong；无效/缺失 token 被拒（close 1008）。
鉴权复用与 HTTP 一致的 JWT + 黑名单逻辑（见 src.api.dependencies.ws_auth）。
"""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.config.settings import get_settings
from src.domain.services.token_service import TokenService
from src.infrastructure.lifecycle import empty_lifespan
from src.main import create_app


@pytest.mark.integration
class TestRealtimeWebSocket:
    @pytest.fixture
    def app(self):
        return create_app(lifespan_override=empty_lifespan)

    @staticmethod
    def _valid_token() -> str:
        s = get_settings()
        ts = TokenService(
            secret_key=s.JWT_SECRET_KEY,
            algorithm=s.JWT_ALGORITHM,
            access_expire_minutes=s.ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_expire_days=s.REFRESH_TOKEN_EXPIRE_DAYS,
        )
        return ts.create_access_token({"sub": "ws-test-user"})

    def test_connect_receives_connected_and_pong(self, app):
        token = self._valid_token()
        client = TestClient(app)
        with client.websocket_connect(f"/api/system/ws?token={token}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connected"
            assert msg["data"]["user_id"] == "ws-test-user"
            ws.send_json({"type": "ping"})
            pong = ws.receive_json()
            assert pong["type"] == "pong"

    def test_invalid_token_closed(self, app):
        client = TestClient(app)
        with (
            client.websocket_connect("/api/system/ws?token=not.a.valid.jwt") as ws,
            pytest.raises(WebSocketDisconnect) as exc,
        ):
            ws.receive_json()
        assert exc.value.code == 1008

    def test_missing_token_closed(self, app):
        client = TestClient(app)
        with client.websocket_connect("/api/system/ws") as ws, pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 1008
