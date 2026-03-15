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
    print("=== 2. 创建测试用户 ===")
    # 先尝试登录，如果用户存在则跳过创建
    resp = httpx.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "testuser", "password": "TestPass123"},
    )

    if resp.status_code == 200:
        print("用户已存在，跳过创建")
        data = resp.json()
        return data.get("access_token")
    elif resp.status_code == 401:
        # 用户不存在，尝试创建（需要权限，可能会失败）
        print("用户不存在，尝试创建...")
        resp = httpx.post(
            f"{BASE_URL}/api/v1/users",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
                "full_name": "测试用户",
            },
        )
        print(f"创建用户状态码: {resp.status_code}")
        if resp.status_code in (201, 401, 403):
            # 需要权限，使用数据库中已有的用户测试
            print("需要权限创建用户，使用数据库已有用户测试")
        print()
        return None


def test_login():
    """测试登录"""
    print("=== 3. 用户登录 ===")
    resp = httpx.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "testuser", "password": "TestPass123"},
    )
    print(f"状态码: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        print(f"Access Token: {data['access_token'][:50]}...")
        print(f"Refresh Token: {data['refresh_token'][:50]}...")
        print(f"Token Type: {data['token_type']}")
        print()
        return data.get("access_token")
    else:
        print(f"登录失败: {resp.json()}")
        print()
        return None


def test_protected_endpoint(token: str):
    """测试受保护的端点"""
    print("=== 4. 获取当前用户信息 (需要认证) ===")
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    print()
    return resp.status_code == 200


def test_update_profile(token: str):
    """测试更新个人资料"""
    print("=== 5. 更新个人资料 ===")
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.put(
        f"{BASE_URL}/api/v1/users/me",
        headers=headers,
        json={"full_name": "更新后的用户名"},
    )
    print(f"状态码: {resp.status_code}")
    print(f"响应: {resp.json()}")
    print()
    return resp.status_code == 200


def test_rbac_endpoints(token: str):
    """测试 RBAC 端点"""
    print("=== 6. 获取角色列表 ===")
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(f"{BASE_URL}/api/v1/rbac/roles", headers=headers)
    print(f"状态码: {resp.status_code}")
    if resp.status_code == 200:
        roles = resp.json()
        print(f"角色数量: {len(roles)}")
        for role in roles:
            print(f"  - {role['name']}: {role['description']}")
    else:
        print(f"响应: {resp.json()}")
    print()

    print("=== 7. 获取权限列表 ===")
    resp = httpx.get(f"{BASE_URL}/api/v1/rbac/permissions", headers=headers)
    print(f"状态码: {resp.status_code}")
    if resp.status_code == 200:
        perms = resp.json()
        print(f"权限数量: {len(perms)}")
        for perm in perms[:5]:  # 只显示前5个
            print(f"  - {perm['codename']}: {perm['name']}")
    else:
        print(f"响应: {resp.json()}")
    print()


def test_no_auth():
    """测试未认证访问"""
    print("=== 8. 测试未认证访问受保护端点 ===")
    resp = httpx.get(f"{BASE_URL}/api/v1/auth/me")
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
