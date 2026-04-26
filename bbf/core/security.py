"""
密码加密工具
提供密码哈希和验证功能
"""
import os
import secrets
from typing import Optional

import bcrypt


def get_password_hash(password: str, salt: Optional[str] = None) -> str:
    """
    对密码进行哈希加密

    Args:
        password: 明文密码
        salt: 可选的 salt，如果不提供则自动生成

    Returns:
        bcrypt 哈希后的密码字符串
    """
    if salt is None:
        salt = bcrypt.gensalt()

    if isinstance(password, str):
        password = password.encode('utf-8')

    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        True if password matches, False otherwise
    """
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')

    return bcrypt.checkpw(plain_password, hashed_password)


def generate_random_password(length: int = 16) -> str:
    """
    生成随机密码

    Args:
        length: 密码长度，默认 16

    Returns:
        随机生成的密码字符串
    """
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def is_password_strong(password: str) -> bool:
    """
    检查密码强度

    Args:
        password: 明文密码

    Returns:
        True if password is strong enough, False otherwise

    Password requirements:
        - 至少 8 个字符
        - 至少包含一个大写字母
        - 至少包含一个小写字母
        - 至少包含一个数字
        - 至少包含一个特殊字符 (!@#$%^&*)
    """
    if len(password) < 8:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()" for c in password)

    return has_upper and has_lower and has_digit and has_special
