"""仪表盘统计聚合接口集成测试（真实 ORM / 会话，无 Mock）。

验证 GET /api/system/dashboard/stats：
- 登录态请求 200 + code 0 + 契约形状（totals 六键、trend 7 项、recentLogs 字段）
- 成功登录才计入趋势/今日登录数；module None 归入「未知」
- creator 经批量映射回填用户名；未登录 401
"""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlmodel import select

from src.infrastructure.database.models import LoginLog, SystemLog, User


@pytest.mark.integration
class TestDashboardApi:
    async def test_dashboard_stats_shape(self, client: AsyncClient, db_session, auth_headers: dict):
        """登录态请求返回完整聚合结构；种子数据与聚合结果对拍。"""
        # ---- 种子数据：今日成功登录 2 + 失败 1；操作日志 user 模块（带 creator）+ None 模块 ----
        now = datetime.now()
        operator = (await db_session.exec(select(User).where(User.username == "authtestuser"))).first()
        assert operator is not None

        db_session.add(LoginLog(status=1, username="authtestuser", created_time=now, ipaddress="127.0.0.1"))
        db_session.add(
            LoginLog(status=1, username="authtestuser", created_time=now - timedelta(hours=2), ipaddress="127.0.0.1")
        )
        db_session.add(LoginLog(status=0, username="intruder", created_time=now, ipaddress="10.0.0.1"))
        db_session.add(
            SystemLog(
                module="user",
                method="POST",
                path="/api/system/user",
                ipaddress="127.0.0.1",
                status_code=200,
                creator_id=operator.id,
                created_time=now,
            )
        )
        db_session.add(
            SystemLog(
                module=None,
                method="GET",
                path="/api/system/unknown",
                ipaddress="127.0.0.1",
                status_code=200,
                created_time=now,
            )
        )
        await db_session.commit()

        r = await client.get("/api/system/dashboard/stats", headers=auth_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["code"] == 0
        data = body["data"]

        # ---- totals：六键齐全，均为整数；auth_headers 建了 1 个超管用户 ----
        assert set(data["totals"].keys()) == {"users", "roles", "menus", "depts", "posts", "online"}
        assert all(isinstance(v, int) for v in data["totals"].values())
        assert data["totals"]["users"] >= 1

        # ---- todayStats：仅成功登录计入（失败 1 条不计）----
        assert data["todayStats"]["loginCount"] == 2
        assert data["todayStats"]["opCount"] == 2

        # ---- loginTrend：7 项、MM-DD 文本、按时间升序、今日计数 2 ----
        trend = data["loginTrend"]
        assert len(trend) == 7
        assert all(set(point.keys()) == {"date", "count"} for point in trend)
        assert trend[-1]["date"] == now.strftime("%m-%d")
        assert trend[-1]["count"] == 2

        # ---- opDistribution：module None 归入「未知」----
        distribution = {item["module"]: item["count"] for item in data["opDistribution"]}
        assert distribution.get("user") == 1
        assert distribution.get("未知") == 1

        # ---- recentLogs：字段形状 + creator 批量映射（creator_id 缺失回填空串）----
        logs = data["recentLogs"]
        assert len(logs) == 2
        expected_keys = {"id", "module", "method", "path", "ipaddress", "creator", "statusCode", "createdTime"}
        assert all(set(log.keys()) == expected_keys for log in logs)
        with_creator = next(log for log in logs if log["module"] == "user")
        assert with_creator["creator"] == "authtestuser"
        assert with_creator["statusCode"] == 200
        assert next(log for log in logs if log["module"] is None)["creator"] == ""

    async def test_dashboard_requires_auth(self, client: AsyncClient):
        """未登录访问返回 401。"""
        r = await client.get("/api/system/dashboard/stats")
        assert r.status_code == 401
