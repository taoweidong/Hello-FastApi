"""认证领域 - 密码哈希服务。

提供密码哈希和验证功能的领域服务。
使用 bcrypt 算法进行安全的密码哈希处理。

bcrypt（cost=12）单次哈希/验证约 200-300ms 纯 CPU 计算，
若直接在 async 调用链中同步执行会阻塞整个事件循环，
因此统一通过 ``anyio.to_thread`` 移入线程池执行。
"""

import hashlib

import anyio.to_thread
import bcrypt


class PasswordService:
    """密码操作的领域服务。

    提供密码哈希和验证的异步方法，用于用户认证场景。
    """

    _BCRYPT_MAX_LENGTH = 72

    @staticmethod
    def _preprocess_password(password: str) -> bytes:
        """超长密码预处理：超过 bcrypt 72 字节输入限制时先做 SHA-256 摘要。"""
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > PasswordService._BCRYPT_MAX_LENGTH:
            password_bytes = hashlib.sha256(password_bytes).digest()
        return password_bytes

    @staticmethod
    def _hash_password_sync(password: str) -> str:
        """bcrypt 哈希的同步实现（仅供线程池调用）。"""
        password_bytes = PasswordService._preprocess_password(password)
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def _verify_password_sync(plain_password: str, hashed_password: str) -> bool:
        """bcrypt 验证的同步实现（仅供线程池调用）。"""
        password_bytes = PasswordService._preprocess_password(plain_password)
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))

    @staticmethod
    async def hash_password(password: str) -> str:
        """对明文密码进行哈希（在线程池中执行，不阻塞事件循环）。

        Args:
            password: 明文密码

        Returns:
            哈希后的密码字符串
        """
        return await anyio.to_thread.run_sync(PasswordService._hash_password_sync, password)

    @staticmethod
    async def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证明文密码与哈希值是否匹配（在线程池中执行，不阻塞事件循环）。

        Args:
            plain_password: 明文密码
            hashed_password: 哈希后的密码

        Returns:
            密码是否匹配
        """
        return await anyio.to_thread.run_sync(PasswordService._verify_password_sync, plain_password, hashed_password)
