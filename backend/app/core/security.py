"""
安全模块：JWT 生成/验证、密码哈希与校验。
所有认证相关操作集中在此，方便统一审计和升级算法。
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt 密码上下文（自动处理 salt 和 pepper）
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── 密码处理 ──────────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """对明文密码进行 bcrypt 哈希，返回可存储的哈希字符串。"""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    return _pwd_context.verify(plain_password, hashed_password)


# ─── JWT Token ────────────────────────────────────────────────────────────

def create_access_token(
    subject: Any,
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    生成 Access Token。

    :param subject:     Token 主题，通常为用户 ID（字符串化）
    :param extra_claims: 附加的自定义 claims（如 role, username）
    :param expires_delta: 自定义有效期，默认使用配置值
    :return: 编码后的 JWT 字符串
    """
    expire_delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expire_delta,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any) -> str:
    """
    生成 Refresh Token（有效期更长，仅用于换取新 Access Token）。
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    解码并校验 JWT Token。

    :raises JWTError: Token 无效或已过期时抛出
    :return: 解码后的 payload 字典
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def get_token_subject(token: str) -> Optional[str]:
    """
    安全地从 Token 中提取 sub 字段（用户 ID）。
    Token 无效时返回 None，不抛出异常。
    """
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except JWTError:
        return None
