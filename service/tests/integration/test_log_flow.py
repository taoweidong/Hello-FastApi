"""日志管理全流程集成测试：登录日志、操作日志、系统日志。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestLogFlow:
    async def test_list_login_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/login-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["data"]["total"] >= 1

    async def test_batch_delete_login_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/login-logs/batch-delete", headers=h, json={"ids": [flow_seed.login_log_id]}
        )
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] == 1

    async def test_clear_login_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/login-logs/clear", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] >= 0

    async def test_list_operation_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/operation-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_batch_delete_operation_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/operation-logs/batch-delete", headers=h, json={"ids": [flow_seed.system_log_id]}
        )
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] >= 0

    async def test_clear_operation_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/operation-logs/clear", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] >= 0

    async def test_list_system_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/system-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_system_log_detail(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/system-logs-detail", headers=h, json={"id": flow_seed.system_log_id})
        assert r.status_code == 200
        assert r.json()["code"] == 0

    # ============ keyset 深分页 + 响应瘦身契约（列表置 None / 详情全量） ============

    async def _seed_keyset_logs(self, db_session, module: str, count: int = 5):
        """按时间递增插入 count 条审计日志，返回全部 id（id 在构造时即已生成）。"""
        from datetime import datetime, timedelta, timezone

        from src.infrastructure.database.models import SystemLog

        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        ids: list[str] = []
        for i in range(count):
            log = SystemLog(
                module=module,
                path=f"/api/system/{module}/{i}",
                method="POST",
                ipaddress="127.0.0.1",
                created_time=base + timedelta(minutes=i),
                updated_time=base + timedelta(minutes=i),
            )
            db_session.add(log)
            ids.append(log.id)
        await db_session.commit()
        return ids

    async def test_operation_logs_keyset_pagination_walks_all_pages(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData, db_session
    ):
        """keyset 游标翻页覆盖全部数据且无重复，深页复用/兜底 total。"""
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        ids = await self._seed_keyset_logs(db_session, "keyset", count=5)

        page_size = 2
        # 首页（offset 模式）：精确 total
        r = await flow_client.post(
            "/api/system/operation-logs", headers=h, json={"pageNum": 1, "pageSize": page_size, "module": "keyset"}
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["total"] == 5
        page1 = data["list"]
        assert len(page1) == page_size

        # 游标翻页直至空页：断言全部 5 条被覆盖且无重复（DESC 稳定排序 + 行比较）
        seen = [row["id"] for row in page1]
        rows_by_id = {row["id"]: row for row in page1}
        while True:
            last_row = rows_by_id[seen[-1]]
            r = await flow_client.post(
                "/api/system/operation-logs",
                headers=h,
                json={
                    "pageSize": page_size,
                    "module": "keyset",
                    "beforeTime": last_row["createdTime"],
                    "beforeId": last_row["id"],
                },
            )
            assert r.status_code == 200
            rows = r.json()["data"]["list"]
            if not rows:
                break
            for row in rows:
                rows_by_id[row["id"]] = row
                seen.append(row["id"])
        assert sorted(seen) == sorted(ids)
        assert len(set(seen)) == 5

    async def test_operation_logs_slim_list_and_full_detail(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData, db_session
    ):
        """列表行 body/responseResult 置 None；详情接口返回全量大字段。"""
        from datetime import datetime, timezone

        from src.infrastructure.database.models import SystemLog

        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        log = SystemLog(
            module="slim",
            path="/api/system/slim",
            method="POST",
            ipaddress="127.0.0.1",
            body='{"password": "secret"}',
            response_result="created",
            created_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
            updated_time=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        db_session.add(log)
        await db_session.commit()

        r = await flow_client.post(
            "/api/system/operation-logs", headers=h, json={"pageNum": 1, "pageSize": 10, "module": "slim"}
        )
        assert r.status_code == 200
        rows = r.json()["data"]["list"]
        assert len(rows) == 1
        # 瘦身契约：列表行不返回大字段
        assert rows[0]["body"] is None
        assert rows[0]["responseResult"] is None

        detail = await flow_client.post("/api/system/system-logs-detail", headers=h, json={"id": rows[0]["id"]})
        assert detail.status_code == 200
        detail_data = detail.json()["data"]
        # 详情契约：全量大字段
        assert detail_data["body"] == '{"password": "secret"}'
        assert detail_data["responseResult"] == "created"
