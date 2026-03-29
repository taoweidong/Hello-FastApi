"""用户领域包。"""

from src.domain.user.repository import UserRepositoryInterface
from src.infrastructure.database.models import User

__all__ = ["User", "UserRepositoryInterface"]
