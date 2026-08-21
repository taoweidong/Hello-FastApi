"""临时脚本：后端全量 API 冒烟——9 大模块 CRUD 全链路 + 特殊端点全覆盖。

覆盖模块：用户、角色、菜单、部门、字典、公告、岗位、IP规则、系统配置
"""

import time

import httpx

BASE = "http://localhost:8000/api/system"
SUFFIX = time.strftime("%m%d%H%M%S")


def get_token(client: httpx.Client) -> str:
    resp = client.post(f"{BASE}/login", json={"username": "admin", "password": "admin123"}, timeout=60)
    data = resp.json()["data"]
    return data["accessToken"], data["refreshToken"]


def main() -> None:
    with httpx.Client(timeout=30) as client:
        token, refresh = get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        print("=== 登录成功 ===\n")

        # ============ 9 大模块 CRUD ============
        modules = [
            ("用户", "/user", {"username": f"smoke_{SUFFIX}", "password": "Test123456", "nickname": "烟测用户"}),
            ("角色", "/role", {"name": f"烟测角色{SUFFIX}", "code": f"smoke_role_{SUFFIX}"}),
            ("菜单", "/menu", {"name": f"烟测菜单{SUFFIX}", "menuType": 1, "path": f"/smoke/{SUFFIX}"}),
            ("部门", "/dept", {"name": f"烟测部门{SUFFIX}"}),
            (
                "字典",
                "/dictionary",
                {"name": f"烟测字典{SUFFIX}", "label": f"烟测标签{SUFFIX}", "value": f"smoke_{SUFFIX}", "sort": 1},
            ),
            ("公告", "/notice", {"title": f"烟测公告{SUFFIX}", "content": "烟测内容", "noticeType": 1}),
            ("岗位", "/post", {"postCode": f"smoke_{SUFFIX}", "postName": f"烟测岗位{SUFFIX}"}),
            ("IP规则", "/ip-rule", {"ipAddress": "10.9.9.9", "ruleType": "blacklist", "reason": "烟测"}),
            ("系统配置", "/config", {"key": f"smoke.key.{SUFFIX}", "value": "1", "description": "烟测"}),
        ]

        no_detail = {"menu", "dept", "dictionary"}  # 设计上无 GET /{id} 详情端点

        for name, prefix, create_body in modules:
            # 1. 创建
            r = client.post(f"{BASE}{prefix}/create", headers=headers, json=create_body)
            rid = ""
            if r.status_code in (200, 201):
                rid = str(r.json().get("data", {}).get("id", ""))
            # 2. 分页查询
            r2 = client.post(f"{BASE}{prefix}", headers=headers, json={"pageNum": 1, "pageSize": 10})
            # 3. 详情 / 更新 / 删除
            detail = "无详情端点" if prefix.lstrip("/") in no_detail else "-"
            update = "-"
            delete = "-"
            if rid:
                if detail == "-":
                    r3 = client.get(f"{BASE}{prefix}/{rid}", headers=headers)
                    detail = str(r3.status_code)
                r4 = client.put(f"{BASE}{prefix}/{rid}", headers=headers, json={**create_body, "isActive": 0})
                update = str(r4.status_code)
                r5 = client.delete(f"{BASE}{prefix}/{rid}", headers=headers)
                delete = str(r5.status_code)
            print(
                f"[{name}] create={r.status_code} id={rid[:8] or '-'} list={r2.status_code} "
                f"detail={detail} update={update} delete={delete}"
            )
            if r.status_code not in (200, 201):
                print(f"    响应: {r.text[:200]}")

        # ============ 个人中心与认证 ============
        print("\n=== 认证与个人中心 ===")
        r = client.get(f"{BASE}/mine", headers=headers)
        mine_data = r.json().get("data", {})
        print(f"GET /mine -> {r.status_code}, 用户={mine_data.get('username')}")
        # /mine 无 id 字段，从用户列表取当前用户名对应 id
        u0 = client.post(f"{BASE}/user", headers=headers, json={"pageNum": 1, "pageSize": 100}).json().get("data", {})
        u0_rows = u0 if isinstance(u0, list) else u0.get("items") or u0.get("list") or []
        uid = ""
        for row in u0_rows:
            if row.get("username") == mine_data.get("username"):
                uid = str(row.get("id", ""))
                break
        r = client.get(f"{BASE}/mine-logs", headers=headers)
        print(f"GET /mine-logs -> {r.status_code}")
        r = client.post(f"{BASE}/list-role-ids", headers=headers, json={"userId": uid})
        print(f"POST /list-role-ids(userId={uid}) -> {r.status_code}")
        r = client.post(f"{BASE}/role-menu", headers=headers, json={})
        print(f"POST /role-menu -> {r.status_code}")
        roles = client.get(f"{BASE}/list-all-role", headers=headers).json().get("data", [])
        first_role_id = str(roles[0].get("id", "")) if roles else ""
        r = client.post(f"{BASE}/role-menu-ids", headers=headers, json={"id": first_role_id})
        print(f"POST /role-menu-ids(roleId={first_role_id}) -> {r.status_code}")
        r = client.post(f"{BASE}/refresh-token", json={"refreshToken": refresh}, timeout=60)
        print(f"POST /refresh-token -> {r.status_code}")

        # 注册新用户
        reg_user = f"reg_{SUFFIX}"
        r = client.post(f"{BASE}/register", json={"username": reg_user, "password": "Test123456"})
        print(f"POST /register({reg_user}) -> {r.status_code} {r.json().get('message', '')[:40]}")

        # ============ 树形与特殊查询 ============
        print("\n=== 树形与特殊查询 ===")
        for path in (
            "/dept/tree",
            "/menu/tree",
            "/menu/user-menus",
            "/post/options",
            "/notice/latest",
            "/server-info",
            "/cache-info",
            "/get-map-info",
            "/user/info",
            "/health",
        ):
            r = (
                client.get(f"{BASE}{path}", headers=headers)
                if path != "/health"
                else client.get("http://localhost:8000/health")
            )
            print(f"GET {path} -> {r.status_code}")

        r = client.post(f"{BASE}/get-card-list", headers=headers, json={})
        print(f"POST /get-card-list -> {r.status_code}")

        # ============ 字典与岗位关联 ============
        d = (
            client.post(f"{BASE}/dictionary", headers=headers, json={"pageNum": 1, "pageSize": 5})
            .json()
            .get("data", {})
        )
        d_rows = d if isinstance(d, list) else d.get("items") or d.get("list") or []
        dict_name = d_rows[0].get("name", "languages") if d_rows else "languages"
        r = client.get(f"{BASE}/dictionary/type/{dict_name}", headers=headers)
        print(f"GET /dictionary/type/{dict_name} -> {r.status_code}")
        r = client.post(f"{BASE}/dictionary/getByName", headers=headers, json={"name": dict_name})
        print(f"POST /dictionary/getByName({dict_name}) -> {r.status_code}")
        u = client.post(f"{BASE}/user", headers=headers, json={"pageNum": 1, "pageSize": 1}).json().get("data", {})
        u_rows = u if isinstance(u, list) else u.get("items") or u.get("list") or []
        uid2 = str(u_rows[0].get("id", "")) if u_rows else ""
        if uid2:
            r = client.get(f"{BASE}/post/user/{uid2}", headers=headers)
            print(f"GET /post/user/{uid2} -> {r.status_code}")

        # ============ 日志与监控 ============
        print("\n=== 日志与监控 ===")
        for path in ("/login-logs", "/operation-logs", "/system-logs"):
            r = client.post(f"{BASE}{path}", headers=headers, json={"pageNum": 1, "pageSize": 5})
            print(f"POST {path} -> {r.status_code}")
        body = client.post(f"{BASE}/system-logs", headers=headers, json={"pageNum": 1, "pageSize": 1})
        if body.status_code == 200:
            d = body.json().get("data", {})
            rows = d if isinstance(d, list) else d.get("items") or d.get("list") or []
            first = rows[0] if rows else {}
            log_id = first.get("id", "")
            r = client.post(f"{BASE}/system-logs-detail", headers=headers, json={"id": log_id})
            print(f"POST /system-logs-detail({log_id}) -> {r.status_code}")
        r = client.post(f"{BASE}/online-logs", headers=headers, json={"pageNum": 1, "pageSize": 5})
        print(f"POST /online-logs -> {r.status_code}")

        # ============ 登出 ============
        r = client.post(f"{BASE}/logout", headers={**headers, "Content-Type": "application/json"}, json={})
        print(f"\nPOST /logout -> {r.status_code}")
        print("\n=== 冒烟完成 ===")


if __name__ == "__main__":
    main()
