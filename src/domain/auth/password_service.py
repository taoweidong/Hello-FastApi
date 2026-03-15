"""认证领域 - 密码哈希工具。"""

import bcrypt


class PasswordService:
    """密码操作的领域服务。"""

    @staticmethod
    def hash_password(password: str) -> str:
        """对明文密码进行哈希。"""
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证明文密码与哈希值是否匹配。"""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
