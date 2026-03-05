"""数据库连接管理

提供MySQL、MongoDB、Redis的连接池管理和会话管理
"""

from typing import AsyncGenerator, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# SQLAlchemy Base类，用于定义ORM模型
Base = declarative_base()

# 全局数据库连接实例
_mysql_engine: Optional[AsyncEngine] = None
_mysql_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_mongodb_client: Optional[AsyncIOMotorClient] = None
_mongodb_database: Optional[AsyncIOMotorDatabase] = None
_redis_pool: Optional[ConnectionPool] = None


# ==================== MySQL连接管理 ====================


def get_mysql_engine() -> AsyncEngine:
    """获取MySQL引擎实例

    Returns:
        AsyncEngine: SQLAlchemy异步引擎

    Raises:
        RuntimeError: 如果引擎未初始化
    """
    if _mysql_engine is None:
        raise RuntimeError("MySQL引擎未初始化，请先调用init_mysql()")
    return _mysql_engine


def get_mysql_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取MySQL会话工厂

    Returns:
        async_sessionmaker: SQLAlchemy会话工厂

    Raises:
        RuntimeError: 如果会话工厂未初始化
    """
    if _mysql_session_factory is None:
        raise RuntimeError("MySQL会话工厂未初始化，请先调用init_mysql()")
    return _mysql_session_factory


async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    """获取MySQL数据库会话（依赖注入）

    用于FastAPI的Depends注入，自动管理会话生命周期

    Yields:
        AsyncSession: 数据库会话

    Example:
        ```python
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_mysql_session)):
            result = await session.execute(select(User))
            return result.scalars().all()
        ```
    """
    session_factory = get_mysql_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_mysql() -> None:
    """初始化MySQL连接池

    在应用启动时调用，创建数据库引擎和会话工厂
    """
    global _mysql_engine, _mysql_session_factory

    settings = get_settings()

    logger.info(
        "初始化MySQL连接池",
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        pool_size=settings.mysql_pool_size,
    )

    # 创建异步引擎
    _mysql_engine = create_async_engine(
        settings.mysql_url,
        echo=settings.mysql_echo,
        pool_size=settings.mysql_pool_size,
        max_overflow=settings.mysql_max_overflow,
        pool_recycle=settings.mysql_pool_recycle,
        pool_pre_ping=True,  # 连接前检查连接是否有效
    )

    # 创建会话工厂
    _mysql_session_factory = async_sessionmaker(
        bind=_mysql_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    logger.info("MySQL连接池初始化成功")


async def close_mysql() -> None:
    """关闭MySQL连接池

    在应用关闭时调用，释放所有数据库连接
    """
    global _mysql_engine, _mysql_session_factory

    if _mysql_engine is not None:
        logger.info("关闭MySQL连接池")
        await _mysql_engine.dispose()
        _mysql_engine = None
        _mysql_session_factory = None
        logger.info("MySQL连接池已关闭")


async def check_mysql_health() -> bool:
    """检查MySQL连接健康状态

    Returns:
        bool: 连接是否健康
    """
    try:
        engine = get_mysql_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("MySQL健康检查失败", error=str(e))
        return False


# ==================== MongoDB连接管理 ====================


def get_mongodb_client() -> AsyncIOMotorClient:
    """获取MongoDB客户端实例

    Returns:
        AsyncIOMotorClient: MongoDB客户端

    Raises:
        RuntimeError: 如果客户端未初始化
    """
    if _mongodb_client is None:
        raise RuntimeError("MongoDB客户端未初始化，请先调用init_mongodb()")
    return _mongodb_client


def get_mongodb_database() -> AsyncIOMotorDatabase:
    """获取MongoDB数据库实例

    Returns:
        AsyncIOMotorDatabase: MongoDB数据库

    Raises:
        RuntimeError: 如果数据库未初始化
    """
    if _mongodb_database is None:
        raise RuntimeError("MongoDB数据库未初始化，请先调用init_mongodb()")
    return _mongodb_database


async def init_mongodb() -> None:
    """初始化MongoDB连接

    在应用启动时调用，创建MongoDB客户端和数据库实例
    """
    global _mongodb_client, _mongodb_database

    settings = get_settings()

    logger.info(
        "初始化MongoDB连接",
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        database=settings.mongodb_database,
    )

    # 创建MongoDB客户端
    _mongodb_client = AsyncIOMotorClient(
        settings.mongodb_url,
        maxPoolSize=settings.mongodb_max_pool_size,
        minPoolSize=settings.mongodb_min_pool_size,
        serverSelectionTimeoutMS=5000,  # 服务器选择超时5秒
    )

    # 获取数据库实例
    _mongodb_database = _mongodb_client[settings.mongodb_database]

    logger.info("MongoDB连接初始化成功")


async def close_mongodb() -> None:
    """关闭MongoDB连接

    在应用关闭时调用，关闭MongoDB客户端
    """
    global _mongodb_client, _mongodb_database

    if _mongodb_client is not None:
        logger.info("关闭MongoDB连接")
        _mongodb_client.close()
        _mongodb_client = None
        _mongodb_database = None
        logger.info("MongoDB连接已关闭")


async def check_mongodb_health() -> bool:
    """检查MongoDB连接健康状态

    Returns:
        bool: 连接是否健康
    """
    try:
        client = get_mongodb_client()
        await client.admin.command("ping")
        return True
    except Exception as e:
        logger.error("MongoDB健康检查失败", error=str(e))
        return False


# ==================== Redis连接管理 ====================


def get_redis_pool() -> ConnectionPool:
    """获取Redis连接池实例

    Returns:
        ConnectionPool: Redis连接池

    Raises:
        RuntimeError: 如果连接池未初始化
    """
    if _redis_pool is None:
        raise RuntimeError("Redis连接池未初始化，请先调用init_redis()")
    return _redis_pool


async def get_redis() -> AsyncGenerator[Redis, None]:
    """获取Redis连接（依赖注入）

    用于FastAPI的Depends注入，自动管理连接生命周期

    Yields:
        Redis: Redis连接

    Example:
        ```python
        @app.get("/cache")
        async def get_cache(redis: Redis = Depends(get_redis)):
            value = await redis.get("key")
            return {"value": value}
        ```
    """
    pool = get_redis_pool()
    redis = Redis(connection_pool=pool)
    try:
        yield redis
    finally:
        await redis.close()


async def init_redis() -> None:
    """初始化Redis连接池

    在应用启动时调用，创建Redis连接池
    """
    global _redis_pool

    settings = get_settings()

    logger.info(
        "初始化Redis连接池",
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
    )

    # 创建Redis连接池
    _redis_pool = ConnectionPool(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password if settings.redis_password else None,
        db=settings.redis_db,
        max_connections=settings.redis_max_connections,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        decode_responses=True,  # 自动解码响应为字符串
    )

    logger.info("Redis连接池初始化成功")


async def close_redis() -> None:
    """关闭Redis连接池

    在应用关闭时调用，关闭Redis连接池
    """
    global _redis_pool

    if _redis_pool is not None:
        logger.info("关闭Redis连接池")
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis连接池已关闭")


async def check_redis_health() -> bool:
    """检查Redis连接健康状态

    Returns:
        bool: 连接是否健康
    """
    try:
        pool = get_redis_pool()
        redis = Redis(connection_pool=pool)
        await redis.ping()
        await redis.close()
        return True
    except Exception as e:
        logger.error("Redis健康检查失败", error=str(e))
        return False


# ==================== 统一初始化和关闭 ====================


async def init_databases() -> None:
    """初始化所有数据库连接

    在应用启动时调用，初始化MySQL、MongoDB、Redis连接
    """
    logger.info("开始初始化数据库连接")

    await init_mysql()
    await init_mongodb()
    await init_redis()

    logger.info("所有数据库连接初始化完成")


async def close_databases() -> None:
    """关闭所有数据库连接

    在应用关闭时调用，关闭MySQL、MongoDB、Redis连接
    """
    logger.info("开始关闭数据库连接")

    await close_mysql()
    await close_mongodb()
    await close_redis()

    logger.info("所有数据库连接已关闭")


async def check_databases_health() -> dict[str, bool]:
    """检查所有数据库连接健康状态

    Returns:
        dict: 各数据库的健康状态
    """
    return {
        "mysql": await check_mysql_health(),
        "mongodb": await check_mongodb_health(),
        "redis": await check_redis_health(),
    }
