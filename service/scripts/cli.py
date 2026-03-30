"""FastAPI 管理命令行工具。

使用方式:
    python -m scripts.cli runserver
    python -m scripts.cli createsuperuser --username admin --password admin123 --email admin@example.com
    python -m scripts.cli initdb
    python -m scripts.cli seedrbac
    python -m scripts.cli seeddata  # 初始化测试数据（菜单、日志等）
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn

from src.config.settings import settings


def run_server() -> None:
    """启动开发服务器。"""
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


async def create_superuser(
    username: str, email: str, password: str, nickname: str | None = None
) -> None:
    """创建超级管理员。"""
    from src.application.dto.user_dto import UserCreateDTO
    from src.application.services.user_service import UserService
    from src.infrastructure.database import async_session_factory, init_db

    await init_db()

    dto = UserCreateDTO(
        username=username,
        email=email,
        password=password,
        nickname=nickname,
    )

    async with async_session_factory() as session:
        service = UserService(session)
        user = await service.create_superuser(dto)
        await session.commit()
        print(f"超级管理员 '{user.username}' 创建成功 (id: {user.id})")


async def init_database() -> None:
    """初始化数据库表。"""
    from src.infrastructure.database import init_db

    await init_db()
    print("数据库表创建成功")


async def seed_rbac() -> None:
    """初始化默认角色和权限。"""
    from src.core.constants import DEFAULT_PERMISSIONS, DEFAULT_ROLES
    from src.infrastructure.database import async_session_factory, init_db
    from src.infrastructure.database.models import Permission, Role
    from src.infrastructure.repositories.rbac_repository import (
        PermissionRepository,
        RoleRepository,
    )

    await init_db()

    async with async_session_factory() as session:
        role_repo = RoleRepository(session)
        perm_repo = PermissionRepository(session)

        # 创建默认权限
        for perm_data in DEFAULT_PERMISSIONS:
            existing = await perm_repo.get_by_code(perm_data["code"])
            if existing is None:
                perm = Permission(**perm_data)
                await perm_repo.create(perm)
                print(f"  创建权限: {perm_data['code']}")

        # 创建默认角色
        for name, description in DEFAULT_ROLES.items():
            existing = await role_repo.get_by_name(name)
            if existing is None:
                role = Role(name=name, code=name, description=description, status=1)
                await role_repo.create(role)
                print(f"  创建角色: {name}")

        await session.commit()
        print("RBAC 初始数据创建成功")


async def seed_data() -> None:
    """初始化测试数据（菜单、日志等）。"""
    from datetime import datetime, timedelta
    import random
    from sqlmodel import select
    from src.infrastructure.database import async_session_factory, init_db
    from src.infrastructure.database.models import (
        Menu, LoginLog, OperationLog, SystemLog
    )

    await init_db()

    async with async_session_factory() as session:
        # ========== 1. 初始化菜单数据 ==========
        print("正在检查菜单数据...")
        result = await session.exec(select(Menu))
        existing_menus = result.all()
        
        if not existing_menus:
            print("  添加系统菜单...")
            menus_data = [
                # 系统管理
                {"id": "1", "name": "System", "path": "/system", "component": "", "icon": "ri:settings-3-line", "title": "系统管理", "order_num": 1, "parent_id": None},
                {"id": "11", "name": "User", "path": "/system/user/index", "component": "system/user/index", "icon": "ri:admin-line", "title": "用户管理", "order_num": 1, "parent_id": "1", "permissions": "user:view"},
                {"id": "12", "name": "Role", "path": "/system/role/index", "component": "system/role/index", "icon": "ri:admin-fill", "title": "角色管理", "order_num": 2, "parent_id": "1", "permissions": "role:view"},
                {"id": "13", "name": "Dept", "path": "/system/dept/index", "component": "system/dept/index", "icon": "ri:git-branch-line", "title": "部门管理", "order_num": 3, "parent_id": "1"},
                {"id": "14", "name": "Menu", "path": "/system/menu/index", "component": "system/menu/index", "icon": "ep:menu", "title": "菜单管理", "order_num": 4, "parent_id": "1", "permissions": "menu:view"},
                
                # 系统监控
                {"id": "2", "name": "Monitor", "path": "/monitor", "component": "", "icon": "ep:monitor", "title": "系统监控", "order_num": 2, "parent_id": None},
                {"id": "21", "name": "OnlineUser", "path": "/monitor/online-user", "component": "monitor/online/index", "icon": "ri:user-voice-line", "title": "在线用户", "order_num": 1, "parent_id": "2"},
                {"id": "22", "name": "LoginLog", "path": "/monitor/login-logs", "component": "monitor/logs/login/index", "icon": "ri:window-line", "title": "登录日志", "order_num": 2, "parent_id": "2"},
                {"id": "23", "name": "OperationLog", "path": "/monitor/operation-logs", "component": "monitor/logs/operation/index", "icon": "ri:history-fill", "title": "操作日志", "order_num": 3, "parent_id": "2"},
                {"id": "24", "name": "SystemLog", "path": "/monitor/system-logs", "component": "monitor/logs/system/index", "icon": "ri:file-list-2-line", "title": "系统日志", "order_num": 4, "parent_id": "2"},
                
                # 权限管理
                {"id": "3", "name": "Permission", "path": "/permission", "component": "", "icon": "ep:lollipop", "title": "权限管理", "order_num": 3, "parent_id": None},
                {"id": "31", "name": "PermissionPage", "path": "/permission/page/index", "component": "permission/page/index", "icon": "ep:document", "title": "页面权限", "order_num": 1, "parent_id": "3"},
                {"id": "32", "name": "PermissionButton", "path": "/permission/button/router", "component": "permission/button/index", "icon": "ep:mouse", "title": "按钮权限", "order_num": 2, "parent_id": "3"},
            ]
            
            for menu_data in menus_data:
                menu = Menu(**menu_data)
                session.add(menu)
            print(f"    创建 {len(menus_data)} 个菜单")
        else:
            print(f"  菜单已存在 ({len(existing_menus)} 条)")

        # ========== 2. 初始化登录日志 ==========
        print("正在检查登录日志...")
        result = await session.exec(select(LoginLog))
        existing_logs = result.all()
        
        if not existing_logs:
            print("  添加登录日志测试数据...")
            usernames = ["admin", "user1", "user2", "guest"]
            browsers = ["Chrome 120", "Firefox 121", "Safari 17", "Edge 120"]
            systems = ["Windows 11", "macOS 14", "Ubuntu 22.04", "iOS 17"]
            addresses = ["中国广东省深圳市", "中国北京市", "中国上海市", "中国浙江省杭州市"]
            behaviors = ["账户登录", "验证码登录", "扫码登录"]
            
            for i in range(20):
                log = LoginLog(
                    username=random.choice(usernames),
                    ip=f"192.168.1.{random.randint(1, 254)}",
                    address=random.choice(addresses),
                    system=random.choice(systems),
                    browser=random.choice(browsers),
                    status=1 if random.random() > 0.1 else 0,
                    behavior=random.choice(behaviors),
                    login_time=datetime.now() - timedelta(hours=random.randint(1, 720))
                )
                session.add(log)
            print("    创建 20 条登录日志")
        else:
            print(f"  登录日志已存在 ({len(existing_logs)} 条)")

        # ========== 3. 初始化操作日志 ==========
        print("正在检查操作日志...")
        result = await session.exec(select(OperationLog))
        existing_logs = result.all()
        
        if not existing_logs:
            print("  添加操作日志测试数据...")
            modules = ["用户管理", "角色管理", "菜单管理", "部门管理", "系统设置"]
            summaries = ["新增用户", "修改角色权限", "删除菜单", "更新部门信息", "修改系统配置"]
            
            for i in range(20):
                log = OperationLog(
                    username="admin",
                    ip=f"192.168.1.{random.randint(1, 254)}",
                    address=random.choice(addresses),
                    system=random.choice(systems),
                    browser=random.choice(browsers),
                    status=1 if random.random() > 0.05 else 0,
                    module=random.choice(modules),
                    summary=random.choice(summaries),
                    operating_time=datetime.now() - timedelta(hours=random.randint(1, 720))
                )
                session.add(log)
            print("    创建 20 条操作日志")
        else:
            print(f"  操作日志已存在 ({len(existing_logs)} 条)")

        # ========== 4. 初始化系统日志 ==========
        print("正在检查系统日志...")
        result = await session.exec(select(SystemLog))
        existing_logs = result.all()
        
        if not existing_logs:
            print("  添加系统日志测试数据...")
            levels = ["INFO", "DEBUG", "WARN", "ERROR"]
            urls = ["/api/system/user", "/api/system/role", "/api/system/menu", "/api/system/dept", "/api/system/login"]
            methods = ["GET", "POST", "PUT", "DELETE"]
            
            for i in range(30):
                log = SystemLog(
                    level=random.choice(levels),
                    module=random.choice(modules),
                    url=random.choice(urls),
                    method=random.choice(methods),
                    ip=f"192.168.1.{random.randint(1, 254)}",
                    address=random.choice(addresses),
                    system=random.choice(systems),
                    browser=random.choice(browsers),
                    takes_time=round(random.uniform(5, 500), 2),
                    request_time=datetime.now() - timedelta(hours=random.randint(1, 720)),
                    request_body='{"page": 1, "pageSize": 10}',
                    response_body='{"code": 200, "message": "success"}'
                )
                session.add(log)
            print("    创建 30 条系统日志")
        else:
            print(f"  系统日志已存在 ({len(existing_logs)} 条)")

        await session.commit()
        print("测试数据初始化完成！")


def main() -> None:
    """管理命令主入口。"""
    parser = argparse.ArgumentParser(description="FastAPI 管理命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # runserver 命令
    subparsers.add_parser("runserver", help="启动开发服务器")

    # createsuperuser 命令
    superuser_parser = subparsers.add_parser("createsuperuser", help="创建超级管理员")
    superuser_parser.add_argument("--username", "-u", required=True, help="用户名")
    superuser_parser.add_argument("--email", "-e", required=True, help="邮箱")
    superuser_parser.add_argument("--password", "-p", required=True, help="密码")
    superuser_parser.add_argument("--nickname", "-n", default=None, help="昵称")

    # initdb 命令
    subparsers.add_parser("initdb", help="初始化数据库表")

    # seedrbac 命令
    subparsers.add_parser("seedrbac", help="初始化RBAC数据")

    # seeddata 命令
    subparsers.add_parser("seeddata", help="初始化测试数据（菜单、日志等）")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "runserver":
        run_server()
    elif args.command == "createsuperuser":
        asyncio.run(create_superuser(args.username, args.email, args.password, args.nickname))
    elif args.command == "initdb":
        asyncio.run(init_database())
    elif args.command == "seedrbac":
        asyncio.run(seed_rbac())
    elif args.command == "seeddata":
        asyncio.run(seed_data())


if __name__ == "__main__":
    main()
