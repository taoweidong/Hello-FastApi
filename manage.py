"""Management script for the FastAPI application."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from config.settings import settings


def run_server() -> None:
    """Run the development server."""
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


async def create_superuser() -> None:
    """Create a superuser interactively."""
    from src.application.dto.user_dto import UserCreateDTO
    from src.application.services.user_service import UserService
    from src.infrastructure.database import async_session_factory, init_db

    await init_db()

    username = input("Username: ")
    email = input("Email: ")
    password = input("Password: ")
    full_name = input("Full name (optional): ") or None

    dto = UserCreateDTO(
        username=username,
        email=email,
        password=password,
        full_name=full_name,
    )

    async with async_session_factory() as session:
        service = UserService(session)
        user = await service.create_superuser(dto)
        await session.commit()
        print(f"Superuser '{user.username}' created successfully (id: {user.id})")


async def init_database() -> None:
    """Initialize database tables."""
    from src.infrastructure.database import init_db

    await init_db()
    print("Database tables created successfully")


async def seed_rbac() -> None:
    """Seed default roles and permissions."""
    from src.core.constants import DEFAULT_PERMISSIONS, DEFAULT_ROLES
    from src.domain.rbac.entities import Permission, Role
    from src.infrastructure.database import async_session_factory, init_db
    from src.infrastructure.repositories.rbac_repository import (
        PermissionRepository,
        RoleRepository,
    )

    await init_db()

    async with async_session_factory() as session:
        role_repo = RoleRepository(session)
        perm_repo = PermissionRepository(session)

        # Create default permissions
        for perm_data in DEFAULT_PERMISSIONS:
            existing = await perm_repo.get_by_codename(perm_data["codename"])
            if existing is None:
                perm = Permission(**perm_data)
                await perm_repo.create(perm)
                print(f"  Created permission: {perm_data['codename']}")

        # Create default roles
        for name, description in DEFAULT_ROLES.items():
            existing = await role_repo.get_by_name(name)
            if existing is None:
                role = Role(name=name, description=description)
                await role_repo.create(role)
                print(f"  Created role: {name}")

        await session.commit()
        print("RBAC seed data created successfully")


def main() -> None:
    """Main entry point for management commands."""
    if len(sys.argv) < 2:
        print("Usage: python manage.py <command>")
        print("")
        print("Available commands:")
        print("  runserver       - Start the development server")
        print("  createsuperuser - Create a superuser")
        print("  initdb          - Initialize database tables")
        print("  seedrbac        - Seed default RBAC data")
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
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)

    handler()


if __name__ == "__main__":
    main()
