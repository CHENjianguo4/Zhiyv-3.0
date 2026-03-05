"""安全相关功能

提供JWT Token生成、验证和密码加密等安全功能
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger

logger = get_logger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """加密密码
    
    Args:
        password: 明文密码
        
    Returns:
        加密后的密码哈希
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码哈希
        
    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """创建访问令牌
    
    Args:
        data: 要编码到token中的数据
        expires_delta: token过期时间，默认使用配置中的值
        
    Returns:
        JWT token字符串
    """
    settings = get_settings()
    
    # 复制数据以避免修改原始数据
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    })
    
    # 生成JWT token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    logger.debug(
        "创建访问令牌",
        user_id=data.get("sub"),
        expires_at=expire.isoformat(),
    )
    
    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """创建刷新令牌
    
    Args:
        data: 要编码到token中的数据
        expires_delta: token过期时间，默认为7天
        
    Returns:
        JWT refresh token字符串
    """
    settings = get_settings()
    
    # 复制数据以避免修改原始数据
    to_encode = data.copy()
    
    # 设置过期时间（刷新令牌有效期更长）
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_refresh_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    })
    
    # 生成JWT token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    
    logger.debug(
        "创建刷新令牌",
        user_id=data.get("sub"),
        expires_at=expire.isoformat(),
    )
    
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """解码JWT token
    
    Args:
        token: JWT token字符串
        
    Returns:
        解码后的payload数据
        
    Raises:
        AuthenticationException: 当token无效或过期时
    """
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as e:
        logger.warning("JWT token解码失败", error=str(e))
        raise AuthenticationException(
            message="无效的认证令牌",
            error_code="INVALID_TOKEN",
        ) from e


def verify_access_token(token: str) -> dict[str, Any]:
    """验证访问令牌
    
    Args:
        token: JWT access token字符串
        
    Returns:
        解码后的payload数据
        
    Raises:
        AuthenticationException: 当token无效、过期或类型不匹配时
    """
    payload = decode_token(token)
    
    # 验证token类型
    if payload.get("type") != "access":
        logger.warning("Token类型不匹配", token_type=payload.get("type"))
        raise AuthenticationException(
            message="无效的令牌类型",
            error_code="INVALID_TOKEN_TYPE",
        )
    
    # 验证必需字段
    if "sub" not in payload:
        logger.warning("Token缺少sub字段")
        raise AuthenticationException(
            message="令牌数据不完整",
            error_code="INVALID_TOKEN_DATA",
        )
    
    return payload


def verify_refresh_token(token: str) -> dict[str, Any]:
    """验证刷新令牌
    
    Args:
        token: JWT refresh token字符串
        
    Returns:
        解码后的payload数据
        
    Raises:
        AuthenticationException: 当token无效、过期或类型不匹配时
    """
    payload = decode_token(token)
    
    # 验证token类型
    if payload.get("type") != "refresh":
        logger.warning("Token类型不匹配", token_type=payload.get("type"))
        raise AuthenticationException(
            message="无效的令牌类型",
            error_code="INVALID_TOKEN_TYPE",
        )
    
    # 验证必需字段
    if "sub" not in payload:
        logger.warning("Token缺少sub字段")
        raise AuthenticationException(
            message="令牌数据不完整",
            error_code="INVALID_TOKEN_DATA",
        )
    
    return payload


def get_user_id_from_token(token: str) -> int:
    """从token中提取用户ID
    
    Args:
        token: JWT token字符串
        
    Returns:
        用户ID
        
    Raises:
        AuthenticationException: 当token无效时
    """
    payload = verify_access_token(token)
    user_id = payload.get("sub")
    
    try:
        return int(user_id)
    except (TypeError, ValueError) as e:
        logger.error("无效的用户ID", user_id=user_id)
        raise AuthenticationException(
            message="无效的用户标识",
            error_code="INVALID_USER_ID",
        ) from e
