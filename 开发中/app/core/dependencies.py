"""FastAPI依赖注入

提供常用的依赖注入函数，用于路由处理器
"""

from typing import AsyncGenerator

from fastapi import Depends, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    get_mongodb_database,
    get_mysql_session,
    get_redis,
)
from app.core.exceptions import AuthenticationException
from app.core.security import get_user_id_from_token
from app.models.user import User
from app.services.auth import get_auth_service

# 导出依赖注入函数，方便在路由中使用
__all__ = [
    "get_db_session",
    "get_mongo_db",
    "get_redis_client",
    "get_current_user",
    "get_current_verified_user",
]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取MySQL数据库会话

    用于FastAPI的Depends注入

    Example:
        ```python
        from fastapi import Depends
        from app.core.dependencies import get_db_session

        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    async for session in get_mysql_session():
        yield session


def get_mongo_db() -> AsyncIOMotorDatabase:
    """获取MongoDB数据库实例

    用于FastAPI的Depends注入

    Example:
        ```python
        from fastapi import Depends
        from app.core.dependencies import get_mongo_db

        @router.get("/posts")
        async def get_posts(db: AsyncIOMotorDatabase = Depends(get_mongo_db)):
            posts = await db.posts.find().to_list(length=100)
            return posts
        ```
    """
    return get_mongodb_database()


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """获取Redis客户端

    用于FastAPI的Depends注入

    Example:
        ```python
        from fastapi import Depends
        from app.core.dependencies import get_redis_client

        @router.get("/cache/{key}")
        async def get_cache(key: str, redis: Redis = Depends(get_redis_client)):
            value = await redis.get(key)
            return {"value": value}
        ```
    """
    async for redis in get_redis():
        yield redis


async def get_current_user(
    authorization: str = Header(..., description="Bearer token"),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """获取当前登录用户

    从Authorization header中提取JWT token并验证，返回当前用户对象

    Args:
        authorization: Authorization header，格式为 "Bearer {token}"
        session: 数据库会话

    Returns:
        当前登录的用户对象

    Raises:
        AuthenticationException: 当token无效或用户不存在时

    Example:
        ```python
        from fastapi import Depends
        from app.core.dependencies import get_current_user
        from app.models.user import User

        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id, "nickname": current_user.nickname}
        ```
    """
    # 验证Authorization header格式
    if not authorization.startswith("Bearer "):
        raise AuthenticationException(
            message="无效的认证格式，应为 Bearer {token}",
            error_code="INVALID_AUTH_FORMAT",
        )

    # 提取token
    token = authorization.replace("Bearer ", "")

    # 从token中获取用户ID
    user_id = get_user_id_from_token(token)

    # 获取用户信息
    auth_service = get_auth_service(session)
    user = await auth_service.get_current_user(user_id)

    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前已认证用户

    要求用户必须完成校园身份认证

    Args:
        current_user: 当前登录用户

    Returns:
        已认证的用户对象

    Raises:
        AuthenticationException: 当用户未完成认证时

    Example:
        ```python
        from fastapi import Depends
        from app.core.dependencies import get_current_verified_user
        from app.models.user import User

        @router.post("/posts")
        async def create_post(
            current_user: User = Depends(get_current_verified_user)
        ):
            # 只有已认证用户才能发布帖子
            pass
        ```
    """
    if not current_user.verified:
        raise AuthenticationException(
            message="需要完成校园身份认证才能执行此操作",
            error_code="VERIFICATION_REQUIRED",
        )

    return current_user


# 简化的别名
get_db = get_db_session
get_redis = get_redis_client


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求管理员权限
    
    验证当前用户是否为管理员
    
    Args:
        current_user: 当前登录用户
    
    Returns:
        管理员用户对象
    
    Raises:
        AuthenticationException: 当用户不是管理员时
    """
    from app.models.user import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise AuthenticationException(
            message="需要管理员权限才能执行此操作",
            error_code="ADMIN_REQUIRED",
        )
    
    return current_user
