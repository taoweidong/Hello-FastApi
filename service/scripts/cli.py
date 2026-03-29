"""FastAPI 管理命令行工具。

使用方式:
    python -m scripts.cli runserver
    python -m scripts.cli createsuperuser
    python -m scripts.cli initdb
    python -m scripts.cli seedrbac
"""

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


async def create_superuser() -> None:
    """交互式创建超级管理员。"""
    from src.application.dto.user_dto import UserCreateDTO
    from src.application.services.user_service import UserService
    from src.infrastructure.database import async_session_factory, init_db

    await init_db()

    username = input("用户名: ")
    email = input("邮箱: ")
    password = input("密码: ")
    nickname = input("昵称 (可选): ") or None

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
    if len(sys.argv) < 2:
        print("使用方式: python -m scripts.cli <命令>")
        print("")
        print("可用命令:")
        print("  runserver       - 启动开发服务器")
        print("  createsuperuser - 创建超级管理员")
        print("  initdb          - 初始化数据库表")
        print("  seedrbac        - 初始化RBAC数据")
        return

    command = sys.argv[1]

    commands = {
        "runserver": run_server,
        "createsuperuser": lambda: asyncio.run(create_superuser()),
        "initdb": lambda: asyncio.run(init_database()),
        "seedrbac": lambda: asyncio.run(seed_rbac()),
    }

    handler = commands.get(command)
    if handler is None:
        print(f"未知命令: {command}")
        print(f"可用命令: {', '.join(commands.keys())}")
        sys.exit(1)

    handler()


if __name__ == "__main__":
    main()
