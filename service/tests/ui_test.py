"""前后端联调 UI 自动化测试脚本。

使用 Playwright 进行浏览器自动化测试，覆盖所有页面功能。
"""

import json
import time
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

BASE_URL = "http://localhost:8848"
API_URL = "http://localhost:8000"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

# 记录所有发现的问题
issues: list[dict] = []


def screenshot(page: Page, name: str):
    """保存截图。"""
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  截图: {path}")


def record_issue(page: Page, category: str, page_name: str, description: str, severity: str = "functional"):
    """记录问题。"""
    issue = {
        "category": category,
        "page": page_name,
        "description": description,
        "severity": severity,
        "url": page.url,
    }
    issues.append(issue)
    print(f"  !! 问题 [{severity}] {category}: {description}")


def wait_for_api_response(page: Page, url_pattern: str, timeout: int = 10000):
    """等待特定API响应。"""
    try:
        with page.expect_response(url_pattern, timeout=timeout) as resp:
            return resp
    except Exception:
        return None


def test_login(page: Page):
    """测试登录页面。"""
    print("\n=== 测试登录页面 ===")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    screenshot(page, "01_login_page")

    # 检查登录表单存在
    username_input = page.locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]').first
    password_input = page.locator('input[type="password"], input[placeholder*="密码"]').first

    if username_input.count() == 0 or password_input.count() == 0:
        # 尝试其他选择器
        username_input = page.locator("input").first
        password_input = page.locator('input[type="password"]').first

    try:
        expect(username_input).to_be_visible(timeout=5000)
    except Exception:
        record_issue(page, "前端", "登录", "登录表单未找到用户名输入框", "blocking")
        return False

    # 输入凭据
    username_input.fill("admin")
    password_input.fill("admin123")
    screenshot(page, "02_login_filled")

    # 点击登录按钮
    login_btn = page.locator('button:has-text("登录"), button[type="submit"]').first
    try:
        expect(login_btn).to_be_visible(timeout=5000)
        login_btn.click()
    except Exception:
        record_issue(page, "前端", "登录", "登录按钮未找到", "blocking")
        return False

    # 等待登录完成
    try:
        page.wait_for_url("**/welcome**", timeout=10000)
    except Exception:
        try:
            page.wait_for_url("**/dashboard**", timeout=5000)
        except Exception:
            # 检查是否还在登录页
            if "/login" in page.url:
                record_issue(page, "后端", "登录", "登录失败，仍在登录页", "blocking")
                return False

    page.wait_for_load_state("networkidle")
    screenshot(page, "03_login_success")
    print("  登录成功!")
    return True


def test_user_management(page: Page):
    """测试用户管理页面。"""
    print("\n=== 测试用户管理页面 ===")
    page.goto(f"{BASE_URL}/system/user")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "04_user_list")

    # 检查用户列表
    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            rows = page.locator(".el-table__body-wrapper .el-table__row, tbody tr")
            print(f"  用户列表行数: {rows.count()}")
        except Exception:
            record_issue(page, "前端", "用户管理", "用户列表表格未显示", "functional")
    else:
        record_issue(page, "前端", "用户管理", "用户列表表格未找到", "functional")

    # 测试新增按钮
    add_btn = page.locator('button:has-text("新增"), button:has-text("添加"), button:has-text("新建")').first
    if add_btn.count() > 0:
        try:
            add_btn.click()
            time.sleep(1)
            screenshot(page, "05_user_add_dialog")
            # 检查表单对话框
            dialog = page.locator(".el-dialog, .el-drawer").first
            if dialog.count() > 0:
                expect(dialog).to_be_visible(timeout=3000)
                print("  新增用户对话框正常打开")
                # 关闭对话框
                close_btn = page.locator(".el-dialog__headerbtn, button:has-text('取消')").first
                if close_btn.count() > 0:
                    close_btn.click()
                    time.sleep(0.5)
            else:
                record_issue(page, "前端", "用户管理", "新增用户对话框未显示", "functional")
        except Exception as e:
            record_issue(page, "前端", "用户管理", f"新增用户操作异常: {e}", "functional")
    else:
        record_issue(page, "前端", "用户管理", "新增用户按钮未找到", "functional")

    # 测试搜索
    search_input = page.locator(
        '.el-table__header-wrapper input, '
        'input[placeholder*="搜索"], '
        'input[placeholder*="用户名"]'
    ).first
    if search_input.count() > 0:
        search_input.fill("admin")
        time.sleep(1)
        screenshot(page, "06_user_search")
        search_input.clear()
        time.sleep(0.5)


def test_role_management(page: Page):
    """测试角色管理页面。"""
    print("\n=== 测试角色管理页面 ===")
    page.goto(f"{BASE_URL}/system/role")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "07_role_list")

    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            rows = page.locator(".el-table__body-wrapper .el-table__row, tbody tr")
            print(f"  角色列表行数: {rows.count()}")
        except Exception:
            record_issue(page, "前端", "角色管理", "角色列表表格未显示", "functional")
    else:
        record_issue(page, "前端", "角色管理", "角色列表表格未找到", "functional")


def test_department_management(page: Page):
    """测试部门管理页面。"""
    print("\n=== 测试部门管理页面 ===")
    page.goto(f"{BASE_URL}/system/dept")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "08_dept_list")

    # 部门可能使用树形结构
    tree = page.locator(".el-tree, .el-table, table").first
    if tree.count() > 0:
        try:
            expect(tree).to_be_visible(timeout=5000)
            print("  部门列表/树正常显示")
        except Exception:
            record_issue(page, "前端", "部门管理", "部门列表未显示", "functional")
    else:
        record_issue(page, "前端", "部门管理", "部门列表/树未找到", "functional")


def test_menu_management(page: Page):
    """测试菜单管理页面。"""
    print("\n=== 测试菜单管理页面 ===")
    page.goto(f"{BASE_URL}/system/menu")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "09_menu_list")

    tree = page.locator(".el-tree, .el-table, table").first
    if tree.count() > 0:
        try:
            expect(tree).to_be_visible(timeout=5000)
            print("  菜单列表/树正常显示")
        except Exception:
            record_issue(page, "前端", "菜单管理", "菜单列表未显示", "functional")
    else:
        record_issue(page, "前端", "菜单管理", "菜单列表/树未找到", "functional")


def test_dictionary_management(page: Page):
    """测试字典管理页面。"""
    print("\n=== 测试字典管理页面 ===")
    page.goto(f"{BASE_URL}/system/dict")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "10_dict_list")

    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            print("  字典列表正常显示")
        except Exception:
            record_issue(page, "前端", "字典管理", "字典列表表格未显示", "functional")
    else:
        # 可能是空数据
        empty = page.locator(".el-table__empty-text, .el-empty").first
        if empty.count() > 0:
            print("  字典列表为空（正常，种子数据不含字典）")
        else:
            record_issue(page, "前端", "字典管理", "字典列表表格未找到", "functional")


def test_ip_rules(page: Page):
    """测试IP规则管理页面。"""
    print("\n=== 测试IP规则管理页面 ===")
    page.goto(f"{BASE_URL}/system/ip-rules")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "11_ip_rules_list")

    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            print("  IP规则列表正常显示")
        except Exception:
            record_issue(page, "前端", "IP规则", "IP规则列表表格未显示", "functional")
    else:
        empty = page.locator(".el-table__empty-text, .el-empty").first
        if empty.count() > 0:
            print("  IP规则列表为空（正常，种子数据不含IP规则）")
        else:
            record_issue(page, "前端", "IP规则", "IP规则列表表格未找到", "functional")


def test_system_config(page: Page):
    """测试系统配置页面。"""
    print("\n=== 测试系统配置页面 ===")
    page.goto(f"{BASE_URL}/system/config")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "12_config_list")

    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            print("  系统配置列表正常显示")
        except Exception:
            record_issue(page, "前端", "系统配置", "系统配置列表表格未显示", "functional")
    else:
        empty = page.locator(".el-table__empty-text, .el-empty").first
        if empty.count() > 0:
            print("  系统配置列表为空（正常，种子数据不含系统配置）")
        else:
            record_issue(page, "前端", "系统配置", "系统配置列表表格未找到", "functional")


def test_login_logs(page: Page):
    """测试登录日志页面。"""
    print("\n=== 测试登录日志页面 ===")
    page.goto(f"{BASE_URL}/system/log/login")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "13_login_logs")

    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            rows = page.locator(".el-table__body-wrapper .el-table__row, tbody tr")
            print(f"  登录日志行数: {rows.count()}")
        except Exception:
            record_issue(page, "前端", "登录日志", "登录日志表格未显示", "functional")
    else:
        record_issue(page, "前端", "登录日志", "登录日志表格未找到", "functional")


def test_operation_logs(page: Page):
    """测试操作日志页面。"""
    print("\n=== 测试操作日志页面 ===")
    page.goto(f"{BASE_URL}/system/log/operation")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "14_operation_logs")

    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            rows = page.locator(".el-table__body-wrapper .el-table__row, tbody tr")
            print(f"  操作日志行数: {rows.count()}")
        except Exception:
            record_issue(page, "前端", "操作日志", "操作日志表格未显示", "functional")
    else:
        record_issue(page, "前端", "操作日志", "操作日志表格未找到", "functional")


def test_system_logs(page: Page):
    """测试系统日志页面。"""
    print("\n=== 测试系统日志页面 ===")
    page.goto(f"{BASE_URL}/system/log/system")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "15_system_logs")

    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            rows = page.locator(".el-table__body-wrapper .el-table__row, tbody tr")
            print(f"  系统日志行数: {rows.count()}")
        except Exception:
            record_issue(page, "前端", "系统日志", "系统日志表格未显示", "functional")
    else:
        record_issue(page, "前端", "系统日志", "系统日志表格未找到", "functional")


def test_online_users(page: Page):
    """测试在线用户页面。"""
    print("\n=== 测试在线用户页面 ===")
    page.goto(f"{BASE_URL}/system/online")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    screenshot(page, "16_online_users")

    table = page.locator(".el-table, table").first
    if table.count() > 0:
        try:
            expect(table).to_be_visible(timeout=5000)
            print("  在线用户列表正常显示")
        except Exception:
            record_issue(page, "前端", "在线用户", "在线用户列表表格未显示", "functional")
    else:
        empty = page.locator(".el-table__empty-text, .el-empty").first
        if empty.count() > 0:
            print("  在线用户列表为空")
        else:
            record_issue(page, "前端", "在线用户", "在线用户列表表格未找到", "functional")


def test_api_endpoints(page: Page):
    """通过API直接测试后端端点。"""
    print("\n=== 测试后端API端点 ===")

    # 登录获取token
    login_resp = page.request.post(f"{API_URL}/api/system/login", data=json.dumps({
        "username": "admin",
        "password": "admin123"
    }), headers={"Content-Type": "application/json"})

    if login_resp.ok:
        login_data = login_resp.json()
        print(f"  登录API: 成功 (code={login_data.get('code')})")
        token = login_data.get("data", {}).get("access_token", "")
        if not token:
            # 尝试其他结构
            token = login_data.get("access_token", "")
    else:
        record_issue(page, "后端", "API", f"登录API失败: {login_resp.status}", "blocking")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 测试用户列表API
    resp = page.request.get(f"{API_URL}/api/system/user?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        data = resp.json()
        total = data.get("data", {}).get("total", 0) if isinstance(data.get("data"), dict) else "N/A"
        print(f"  用户列表API: 成功 (total={total})")
    else:
        record_issue(page, "后端", "API", f"用户列表API失败: {resp.status}", "functional")

    # 测试角色列表API
    resp = page.request.get(f"{API_URL}/api/system/role?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        data = resp.json()
        total = data.get("data", {}).get("total", 0) if isinstance(data.get("data"), dict) else "N/A"
        print(f"  角色列表API: 成功 (total={total})")
    else:
        record_issue(page, "后端", "API", f"角色列表API失败: {resp.status}", "functional")

    # 测试菜单树API
    resp = page.request.get(f"{API_URL}/api/system/menu/tree", headers=headers)
    if resp.ok:
        data = resp.json()
        menu_count = len(data.get("data", [])) if isinstance(data.get("data"), list) else "N/A"
        print(f"  菜单树API: 成功 (menus={menu_count})")
    else:
        record_issue(page, "后端", "API", f"菜单树API失败: {resp.status}", "functional")

    # 测试部门列表API
    resp = page.request.get(f"{API_URL}/api/system/dept?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        print("  部门列表API: 成功")
    else:
        record_issue(page, "后端", "API", f"部门列表API失败: {resp.status}", "functional")

    # 测试字典列表API
    resp = page.request.get(f"{API_URL}/api/system/dict?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        print("  字典列表API: 成功")
    else:
        record_issue(page, "后端", "API", f"字典列表API失败: {resp.status}", "functional")

    # 测试IP规则API
    resp = page.request.get(f"{API_URL}/api/system/ip-rules?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        print("  IP规则API: 成功")
    else:
        record_issue(page, "后端", "API", f"IP规则API失败: {resp.status}", "functional")

    # 测试系统配置API
    resp = page.request.get(f"{API_URL}/api/system/config?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        print("  系统配置API: 成功")
    else:
        record_issue(page, "后端", "API", f"系统配置API失败: {resp.status}", "functional")

    # 测试登录日志API
    resp = page.request.get(f"{API_URL}/api/system/log/login?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        data = resp.json()
        total = data.get("data", {}).get("total", 0) if isinstance(data.get("data"), dict) else "N/A"
        print(f"  登录日志API: 成功 (total={total})")
    else:
        record_issue(page, "后端", "API", f"登录日志API失败: {resp.status}", "functional")

    # 测试操作日志API
    resp = page.request.get(f"{API_URL}/api/system/log/operation?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        print("  操作日志API: 成功")
    else:
        record_issue(page, "后端", "API", f"操作日志API失败: {resp.status}", "functional")

    # 测试系统日志API
    resp = page.request.get(f"{API_URL}/api/system/log/system?currentPage=1&pageSize=10", headers=headers)
    if resp.ok:
        data = resp.json()
        total = data.get("data", {}).get("total", 0) if isinstance(data.get("data"), dict) else "N/A"
        print(f"  系统日志API: 成功 (total={total})")
    else:
        record_issue(page, "后端", "API", f"系统日志API失败: {resp.status}", "functional")

    # 测试路由API（动态菜单）
    resp = page.request.get(f"{API_URL}/api/system/router", headers=headers)
    if resp.ok:
        data = resp.json()
        routes = data.get("data", [])
        print(f"  路由API: 成功 (routes={len(routes) if isinstance(routes, list) else 'N/A'})")
    else:
        record_issue(page, "后端", "API", f"路由API失败: {resp.status}", "functional")


def test_sidebar_navigation(page: Page):
    """测试侧边栏导航。"""
    print("\n=== 测试侧边栏导航 ===")
    page.goto(f"{BASE_URL}/welcome")
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    # 查找侧边栏菜单项
    menu_items = page.locator(".sidebar-container .menu-wrap a, .el-menu-item, .el-sub-menu__title")
    count = menu_items.count()
    print(f"  侧边栏菜单项数: {count}")

    if count == 0:
        # 尝试其他选择器
        menu_items = page.locator("[class*='sidebar'] a, [class*='menu'] a, [class*='nav'] a")
        count = menu_items.count()
        print(f"  备用选择器菜单项数: {count}")

    if count == 0:
        record_issue(page, "前端", "导航", "侧边栏菜单项未找到", "functional")


def main():
    """主测试流程。"""
    print("=" * 60)
    print("前后端联调 UI 自动化测试")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # 1. 测试登录
        if not test_login(page):
            print("\n登录失败，终止测试!")
            _print_report()
            browser.close()
            return

        # 2. 测试API端点
        test_api_endpoints(page)

        # 3. 测试侧边栏导航
        test_sidebar_navigation(page)

        # 4. 逐页面UI测试
        test_user_management(page)
        test_role_management(page)
        test_department_management(page)
        test_menu_management(page)
        test_dictionary_management(page)
        test_ip_rules(page)
        test_system_config(page)
        test_login_logs(page)
        test_operation_logs(page)
        test_system_logs(page)
        test_online_users(page)

        browser.close()

    _print_report()


def _print_report():
    """打印测试报告。"""
    print("\n" + "=" * 60)
    print("测试报告")
    print("=" * 60)

    if not issues:
        print("所有测试通过，未发现问题！")
        return

    # 按严重程度分类
    by_severity = {"blocking": [], "functional": [], "experience": []}
    for issue in issues:
        severity = issue.get("severity", "functional")
        if severity not in by_severity:
            severity = "functional"
        by_severity[severity].append(issue)

    print(f"\n共发现 {len(issues)} 个问题：")

    for severity, label in [("blocking", "阻断性"), ("functional", "功能性"), ("experience", "体验性")]:
        items = by_severity[severity]
        if items:
            print(f"\n--- {label} ({len(items)}个) ---")
            for i, issue in enumerate(items, 1):
                print(f"  {i}. [{issue['category']}] {issue['page']}: {issue['description']}")

    # 保存报告到文件
    report_path = Path(__file__).parent / "ui_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存到: {report_path}")
    print(f"截图保存在: {SCREENSHOT_DIR}")


if __name__ == "__main__":
    main()
