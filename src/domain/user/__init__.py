"""User domain package."""

from src.domain.user.entities import User
from src.domain.user.repository import UserRepositoryInterface

__all__ = ["User", "UserRepositoryInterface"]
