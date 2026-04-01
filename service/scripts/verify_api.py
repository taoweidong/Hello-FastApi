"""功能验证脚本 - 测试 API 端点"""

import httpx

BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查端点"""
    print("=== 1. 健康检查 ===")
    resp = httpx.get(f"{BASE_URL}/health")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    print()
    return resp.status_code == 200


def test_user_operations():
    """测试用户操作"""
    print("=== 2. 准备使用 admin 用户测试 ===")
    # 使用创建的超级管理员进行测试
    print("将使用 admin 用户进行后续测试")
    print()
    return None


def test_login():
    """测试登录"""
    print("=== 3. 用户登录 ===")
    # 使用正确的API路径: /api/system/login
    resp = httpx.post(f"{BASE_URL}/api/system/login", json={"username": "admin", "password": "admin123"})
    print(f"状态码: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        # 响应格式: { success, code, message, data: { accessToken, expires, refreshToken, ... } }
        result = data.get("data", {})
        access_token = result.get("accessToken", "")
        refresh_token = result.get("refreshToken", "")
        print(f"Access Token: {access_token[:50] if access_token else 'N/A'}...")
        print(f"Refresh Token: {refresh_token[:50] if refresh_token else 'N/A'}...")
        print()
        return access_token
    else:
        print(f"登录失败: {resp.json()}")
        print()
        return None


def test_protected_endpoint(token: str):
    """测试受保护的端点"""
    print("=== 4. 获取当前用户信息 (需要认证) ===")
    headers = {"Authorization": f"Bearer {token}"}
    # 使用正确的API路径: /api/system/mine
    resp = httpx.get(f"{BASE_URL}/api/system/mine", headers=headers)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    print()
    return resp.status_code == 200


def test_update_profile(token: str):
    """测试获取用户详情"""
    print("=== 5. 获取用户详情 ===")
    headers = {"Authorization": f"Bearer {token}"}
    # 使用正确的API路径: /api/system/user/info
    resp = httpx.get(f"{BASE_URL}/api/system/user/info", headers=headers)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    print()
    return resp.status_code == 200


def test_rbac_endpoints(token: str):
    """测试 RBAC 端点"""
    print("=== 6. 获取角色列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    # 使用正确的API路径: POST /api/system/role
    resp = httpx.post(f"{BASE_URL}/api/system/role", headers=headers, json={"pageNum": 1, "pageSize": 10})
    print(f"状态码: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        roles = data.get("data", {}).get("list", [])
        print(f"角色数量: {len(roles)}")
        for role in roles:
            print(f"  - {role.get('name', 'N/A')}: {role.get('code', 'N/A')}")
    else:
        print(f"响应: {resp.json()}")
    print()

    print("=== 7. 获取权限列表 ===")
    # 使用正确的API路径: GET /api/system/permission/list
    resp = httpx.get(f"{BASE_URL}/api/system/permission/list", headers=headers, params={"pageNum": 1, "pageSize": 10})
    print(f"状态码: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        perms = data.get("data", {}).get("rows", [])
        print(f"权限数量: {len(perms)}")
        for perm in perms[:5]:  # 只显示前5个
            print(f"  - {perm.get('code', 'N/A')}: {perm.get('name', 'N/A')}")
    else:
        print(f"响应: {resp.json()}")
    print()


def test_no_auth():
    """测试未认证访问"""
    print("=== 8. 测试未认证访问受保护端点 ===")
    # 使用正确的API路径: /api/system/mine
    resp = httpx.get(f"{BASE_URL}/api/system/mine")
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    print()
    return resp.status_code in (401, 403)


def main():
    """主测试流程"""
    print("\n" + "=" * 50)
    print("FastAPI + DDD + RBAC 系统功能验证")
    print("=" * 50 + "\n")

    # 1. 健康检查
    if not test_health():
        print("健康检查失败，服务可能未启动")
        return

    # 2. 用户操作
    test_user_operations()

    # 3. 登录
    token = test_login()
    if not token:
        print("登录失败，无法继续测试")
        return

    # 4. 受保护端点
    test_protected_endpoint(token)

    # 5. 更新资料
    test_update_profile(token)

    # 6. RBAC 端点
    test_rbac_endpoints(token)

    # 7. 未认证访问
    test_no_auth()

    print("=" * 50)
    print("功能验证完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
