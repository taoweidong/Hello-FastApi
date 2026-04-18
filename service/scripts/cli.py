"""FastAPI 管理命令行工具。

使用方式:
    python -m scripts.cli runserver
    python -m scripts.cli createsuperuser --username admin --password admin123 --email admin@example.com
    python -m scripts.cli initdb
    python -m scripts.cli seedrbac
    python -m scripts.cli seeddata  # 初始化测试数据（日志等）
    python -m scripts.cli initall  # 一键初始化（表+RBAC+测试数据+超级管理员）
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
    from src.infrastructure.database import close_db, get_async_session_factory, init_db
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
        service = UserService(repo=user_repo, password_service=password_service, role_repo=role_repo)
        user = await service.create_superuser(dto)
        await session.commit()
        print(f"超级管理员 '{user.username}' 创建成功 (id: {user.id})")
        print("  已自动分配 admin 角色，拥有所有菜单权限")

    await close_db()


async def init_database() -> None:
    """初始化数据库表。"""
    from src.infrastructure.database import close_db, init_db

    await init_db()
    await close_db()
    print("数据库表创建成功")


async def seed_rbac() -> None:
    """初始化RBAC数据：创建菜单、角色，并分配权限。"""
    import uuid

    from src.domain.entities.role import RoleEntity
    from src.domain.rbac_defaults import ADMIN_MENU_NAMES, DEFAULT_MENUS, DEFAULT_ROLES, USER_MENU_NAMES
    from src.infrastructure.database import close_db, get_async_session_factory, init_db
    from src.infrastructure.database.models import Menu, MenuMeta
    from src.infrastructure.repositories.menu_repository import MenuRepository
    from src.infrastructure.repositories.role_repository import RoleRepository

    await init_db()

    session_factory = get_async_session_factory()
    async with session_factory() as session:
        menu_repo = MenuRepository(session)
        role_repo = RoleRepository(session)

        # ========== 1. 创建菜单（含MenuMeta） ==========
        print("正在创建菜单...")
        name_to_id: dict[str, str] = {}  # name -> menu.id 映射，用于解析 parent_id
        created_count = 0

        for menu_def in DEFAULT_MENUS:
            # 按name去重，支持幂等执行
            existing = await menu_repo.get_by_name(menu_def["name"])
            if existing:
                name_to_id[menu_def["name"]] = existing.id
                continue

            # 创建 MenuMeta
            meta_data = menu_def.get("meta", {})
            is_show = 0 if menu_def["menu_type"] == 2 else meta_data.get("is_show_menu", 1)
            meta = MenuMeta(
                title=meta_data.get("title", menu_def["name"]),
                icon=meta_data.get("icon", ""),
                is_show_menu=is_show,
                is_show_parent=meta_data.get("is_show_parent", 0),
            )
            session.add(meta)
            await session.flush()

            # 解析 parent_id：从 name_to_id 映射中查找
            raw_parent = menu_def.get("parent_id")
            resolved_parent = name_to_id.get(raw_parent) if raw_parent else None

            # 创建 Menu
            menu = Menu(
                name=menu_def["name"],
                path=menu_def.get("path", ""),
                component=menu_def.get("component"),
                menu_type=menu_def["menu_type"],
                rank=menu_def.get("rank", 0),
                method=menu_def.get("method"),
                parent_id=resolved_parent,
                meta_id=meta.id,
                description=menu_def.get("description"),
            )
            session.add(menu)
            await session.flush()
            name_to_id[menu_def["name"]] = menu.id
            created_count += 1

        if created_count:
            print(f"  创建 {created_count} 个菜单（含权限项）")
        else:
            print("  菜单已存在，跳过创建")

        # ========== 2. 创建默认角色 ==========
        print("正在创建角色...")
        for name, description in DEFAULT_ROLES.items():
            existing = await role_repo.get_by_name(name)
            if existing is None:
                role = RoleEntity(id=uuid.uuid4().hex, name=name, code=name, description=description, is_active=1)
                await role_repo.create(role)
                print(f"  创建角色: {name}")

        # ========== 3. 为 admin 角色分配所有菜单 ==========
        admin_role = await role_repo.get_by_name("admin")
        if admin_role:
            all_menus = await menu_repo.get_all()
            menu_ids = [m.id for m in all_menus]
            if menu_ids:
                await role_repo.assign_menus_to_role(admin_role.id, menu_ids)
                print(f"  admin 角色已分配 {len(menu_ids)} 个菜单权限")

        # ========== 4. 为 user 角色分配只读菜单 ==========
        user_role = await role_repo.get_by_name("user")
        if user_role:
            user_menu_ids = [name_to_id[n] for n in USER_MENU_NAMES if n in name_to_id]
            if user_menu_ids:
                await role_repo.assign_menus_to_role(user_role.id, user_menu_ids)
                print(f"  user 角色已分配 {len(user_menu_ids)} 个菜单权限")

        await session.commit()
        await close_db()
        print("RBAC 初始数据创建成功")


async def seed_data() -> None:
    """初始化测试数据（日志等）。"""
    import random
    import uuid

    from sqlmodel import select

    from src.infrastructure.database import close_db, get_async_session_factory, init_db
    from src.infrastructure.database.models import LoginLog, SystemLog

    await init_db()

    session_factory = get_async_session_factory()
    async with session_factory() as session:
        browsers = ["Chrome 120", "Firefox 121", "Safari 17", "Edge 120"]
        systems = ["Windows 11", "macOS 14", "Ubuntu 22.04", "iOS 17"]

        # ========== 1. 初始化登录日志 ==========
        print("正在检查登录日志...")
        result = await session.exec(select(LoginLog))
        existing_logs = result.all()

        if not existing_logs:
            print("  添加登录日志测试数据...")

            for _ in range(20):
                log = LoginLog(ipaddress=f"192.168.1.{random.randint(1, 254)}", system=random.choice(systems), browser=random.choice(browsers), status=1 if random.random() > 0.1 else 0, login_type=0, creator_id="seed")
                session.add(log)
            print("    创建 20 条登录日志")
        else:
            print(f"  登录日志已存在 ({len(existing_logs)} 条)")

        # ========== 2. 初始化系统日志（sys_logs 表） ==========
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
        await close_db()
        print("测试数据初始化完成！")


async def init_all() -> None:
    """一键初始化：创建表 + RBAC数据 + 测试数据 + 超级管理员。"""
    print("===== 步骤 1/4: 初始化数据库表 =====")
    await init_database()
    print()
    print("===== 步骤 2/4: 初始化RBAC数据 =====")
    await seed_rbac()
    print()
    print("===== 步骤 3/4: 初始化测试数据 =====")
    await seed_data()
    print()
    print("===== 步骤 4/4: 创建超级管理员 =====")
    await create_superuser("admin", "admin@example.com", "admin123", "Administrator")
    print()
    print("全部初始化完成！默认账号: admin / admin123")


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
    subparsers.add_parser("seedrbac", help="初始化RBAC数据（菜单、角色、权限）")

    # seeddata 命令
    subparsers.add_parser("seeddata", help="初始化测试数据（日志等）")

    # initall 命令
    subparsers.add_parser("initall", help="一键初始化（表+RBAC+测试数据+超级管理员）")

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
    elif args.command == "initall":
        asyncio.run(init_all())


if __name__ == "__main__":
    main()
