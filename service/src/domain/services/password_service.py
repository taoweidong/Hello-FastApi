"""认证领域 - 密码哈希服务。

提供密码哈希和验证功能的领域服务。
使用 bcrypt 算法进行安全的密码哈希处理。
"""

import bcrypt


class PasswordService:
    """密码操作的领域服务。

    提供密码哈希和验证的静态方法，用于用户认证场景。
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """对明文密码进行哈希。

        Args:
            password: 明文密码

        Returns:
            哈希后的密码字符串
        """
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证明文密码与哈希值是否匹配。

        Args:
            plain_password: 明文密码
            hashed_password: 哈希后的密码

        Returns:
            密码是否匹配
        """
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
