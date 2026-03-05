"""数据库连接测试

测试MySQL、MongoDB、Redis连接的初始化和健康检查
"""

import pytest

from app.core.database import (
    check_databases_health,
    close_databases,
    get_mongodb_database,
    get_mysql_engine,
    get_redis_pool,
    init_databases,
)


@pytest.mark.asyncio
async def test_database_initialization():
    """测试数据库初始化"""
    # 初始化数据库连接
    await init_databases()

    # 验证MySQL引擎已创建
    mysql_engine = get_mysql_engine()
    assert mysql_engine is not None

    # 验证MongoDB数据库已创建
    mongodb_db = get_mongodb_database()
    assert mongodb_db is not None

    # 验证Redis连接池已创建
    redis_pool = get_redis_pool()
    assert redis_pool is not None

    # 关闭数据库连接
    await close_databases()


@pytest.mark.asyncio
async def test_database_health_check():
    """测试数据库健康检查"""
    # 初始化数据库连接
    await init_databases()

    # 执行健康检查
    health = await check_databases_health()

    # 验证返回结果包含所有数据库
    assert "mysql" in health
    assert "mongodb" in health
    assert "redis" in health

    # 注意：在没有实际数据库服务的情况下，健康检查可能失败
    # 这是预期行为，测试只验证健康检查功能可以正常执行

    # 关闭数据库连接
    await close_databases()


@pytest.mark.asyncio
async def test_mysql_session_context():
    """测试MySQL会话上下文管理"""
    from app.core.database import get_mysql_session

    await init_databases()

    # 测试会话可以正常创建和关闭
    async for session in get_mysql_session():
        assert session is not None
        # 会话应该是活跃的
        assert session.is_active
        break  # 只测试一次

    await close_databases()


@pytest.mark.asyncio
async def test_redis_connection_context():
    """测试Redis连接上下文管理"""
    from app.core.database import get_redis

    await init_databases()

    # 测试Redis连接可以正常创建和关闭
    async for redis in get_redis():
        assert redis is not None
        break  # 只测试一次

    await close_databases()
