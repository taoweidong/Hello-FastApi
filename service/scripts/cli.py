"""FastAPI 管理命令行工具。

使用方式:
    python -m scripts.cli runserver
    python -m scripts.cli createsuperuser --username admin --password admin123 --email admin@example.com
    python -m scripts.cli initdb
    python -m scripts.cli seedrbac
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


if __name__ == "__main__":
    main()
