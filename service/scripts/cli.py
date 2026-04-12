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
    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)


async def create_superuser(username: str, email: str, password: str, nickname: str | None = None) -> None:
    """创建超级管理员。"""
    from src.application.dto.user_dto import UserCreateDTO
    from src.application.services.user_service import UserService
    from src.domain.services.password_service import PasswordService
    from src.infrastructure.database import get_async_session_factory, init_db
    from src.infrastructure.repositories.role_repository import RoleRepository
    from src.infrastructure.repositories.user_repository import UserRepository

    await init_db()

    dto = UserCreateDTO(username=username, email=email, password=password, nickname=nickname)

    session_factory = get_async_session_factory()
    async with session_factory() as session:
        # 使用新的依赖注入模式创建 UserService
        user_repo = UserRepository(session)
        role_repo = RoleRepository(session)
        password_service = PasswordService()
        service = UserService(session=session, repo=user_repo, password_service=password_service, role_repo=role_repo)
        user = await service.create_superuser(dto)
        await session.commit()
        print(f"超级管理员 '{user.username}' 创建成功 (id: {user.id})")


async def init_database() -> None:
    """初始化数据库表。"""
    from src.infrastructure.database import init_db

    await init_db()
    print("数据库表创建成功")


async def seed_rbac() -> None:
    """初始化默认角色。"""
    from src.domain.rbac_defaults import DEFAULT_ROLES
    from src.infrastructure.database import get_async_session_factory, init_db
    from src.infrastructure.database.models import Role
    from src.infrastructure.repositories.role_repository import RoleRepository

    await init_db()

    session_factory = get_async_session_factory()
    async with session_factory() as session:
        role_repo = RoleRepository(session)

        # 创建默认角色
        for name, description in DEFAULT_ROLES.items():
            existing = await role_repo.get_by_name(name)
            if existing is None:
                role = Role(name=name, code=name, description=description, is_active=1)
                await role_repo.create(role)
                print(f"  创建角色: {name}")

        await session.commit()
        print("RBAC 初始数据创建成功")


async def seed_data() -> None:
    """初始化测试数据（菜单、日志等）。"""
    import random
    import uuid

    from sqlmodel import select

    from src.infrastructure.database import get_async_session_factory, init_db
    from src.infrastructure.database.models import LoginLog, Menu, MenuMeta, SystemLog

    await init_db()

    session_factory = get_async_session_factory()
    async with session_factory() as session:
        # ========== 1. 初始化菜单数据 ==========
        print("正在检查菜单数据...")
        result = await session.exec(select(Menu))
        existing_menus = result.all()

        if not existing_menus:
            print("  添加系统菜单...")
            # 菜单定义：(id, name, path, component, icon, title, rank, parent_id, menu_type, description)
            menus_def = [
                # 系统管理（顶级菜单）
                ("1", "System", "/system", "", "ri:settings-3-line", "系统管理", 1, None, 0, "系统管理功能模块入口，包含用户、角色、部门等管理功能"),
                ("11", "User", "/system/user/index", "system/user/index", "ri:admin-line", "用户管理", 1, "1", 0, "管理系统用户账号，支持新增、编辑、删除及角色分配"),
                ("12", "Role", "/system/role/index", "system/role/index", "ri:admin-fill", "角色管理", 2, "1", 0, "管理系统角色定义及菜单权限分配"),
                ("13", "Dept", "/system/dept/index", "system/dept/index", "ri:git-branch-line", "部门管理", 3, "1", 0, "管理组织架构部门层级及人员归属"),
                ("14", "Menu", "/system/menu/index", "system/menu/index", "ep:menu", "菜单管理", 4, "1", 0, "管理系统导航菜单及路由配置"),
                ("15", "IpRule", "/system/ip-rule/index", "system/ip-rule/index", "ri:shield-keyhole-line", "IP规则", 5, "1", 0, "配置 IP 白名单或黑名单访问控制规则"),
                ("16", "SystemConfig", "/system/config/index", "system/config/index", "ri:settings-4-line", "系统配置", 6, "1", 0, "管理系统全局参数及运行配置"),
                ("17", "RolePermission", "/system/permission/index", "system/permission/index", "ri:key-2-line", "角色权限", 7, "1", 0, "为角色分配细粒度的页面及按钮操作权限"),
                # 系统监控（顶级菜单）
                ("2", "Monitor", "/monitor", "", "ep:monitor", "系统监控", 2, None, 0, "系统运行状态监控功能模块入口"),
                ("21", "OnlineUser", "/monitor/online-user", "monitor/online/index", "ri:user-voice-line", "在线用户", 1, "2", 0, "查看当前在线用户列表，支持强制下线操作"),
                ("22", "LoginLog", "/monitor/login-logs", "monitor/logs/login/index", "ri:window-line", "登录日志", 2, "2", 0, "查询用户登录历史记录及登录状态统计"),
                ("23", "OperationLog", "/monitor/operation-logs", "monitor/logs/operation/index", "ri:history-fill", "操作日志", 3, "2", 0, "查询用户操作行为日志及接口调用记录"),
                ("24", "SystemLog", "/monitor/system-logs", "monitor/logs/system/index", "ri:file-list-2-line", "系统日志", 4, "2", 0, "查看系统运行日志及异常错误信息"),
                # 权限管理（顶级菜单）
                ("3", "Permission", "/permission", "", "ep:lollipop", "权限管理", 3, None, 0, "权限演示功能模块，展示页面级和按钮级权限控制"),
                ("31", "PermissionPage", "/permission/page/index", "permission/page/index", "ep:document", "页面权限", 1, "3", 0, "演示基于角色的页面访问权限控制"),
                ("32", "PermissionButton", "/permission/button/router", "permission/button/index", "ep:mouse", "按钮权限", 2, "3", 0, "演示基于角色的按钮操作权限控制"),
            ]

            for menu_id, name, path, component, icon, title, rank, parent_id, menu_type, description in menus_def:
                # 创建 MenuMeta
                meta = MenuMeta(id=uuid.uuid4().hex, title=title, icon=icon, is_show_menu=1, is_show_parent=0)
                session.add(meta)
                await session.flush()  # 确保 meta.id 可用

                # 创建 Menu
                menu = Menu(id=menu_id, name=name, path=path, component=component or None, rank=rank, parent_id=parent_id, menu_type=menu_type, meta_id=meta.id, description=description)
                session.add(menu)

            print(f"    创建 {len(menus_def)} 个菜单（含元数据）")
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

            for _ in range(20):
                log = LoginLog(ipaddress=f"192.168.1.{random.randint(1, 254)}", system=random.choice(systems), browser=random.choice(browsers), status=1 if random.random() > 0.1 else 0, login_type=0, creator_id="seed")
                session.add(log)
            print("    创建 20 条登录日志")
        else:
            print(f"  登录日志已存在 ({len(existing_logs)} 条)")

        # ========== 3. 初始化系统日志（sys_logs 表） ==========
        print("正在检查系统日志...")
        result = await session.exec(select(SystemLog))
        existing_logs = result.all()

        if not existing_logs:
            print("  添加系统日志测试数据...")
            modules = ["user", "role", "menu", "dept", "config", "ip-rule"]
            paths = ["/api/system/user", "/api/system/role", "/api/system/menu", "/api/system/dept", "/api/system/config", "/api/system/ip-rule"]
            methods = ["POST", "PUT", "DELETE"]

            for _ in range(30):
                idx = random.randint(0, len(modules) - 1)
                log = SystemLog(
                    id=uuid.uuid4().hex,
                    module=modules[idx],
                    path=paths[idx],
                    method=random.choice(methods),
                    ipaddress=f"192.168.1.{random.randint(1, 254)}",
                    browser=random.choice(browsers),
                    system=random.choice(systems),
                    response_code=random.choice([200, 201, 204, 400, 404, 500]),
                    status_code=random.choice([200, 201, 204, 400, 404, 500]),
                    creator_id="seed",
                    description=f"种子数据 - {modules[idx]} 操作",
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
