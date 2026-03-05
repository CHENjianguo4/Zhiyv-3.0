"""Pytest配置和共享fixtures"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    close_databases,
    get_mysql_session,
    init_databases,
)
from app.main import create_app
from app.models.user import User, UserProfile


@pytest.fixture(scope="session", autouse=True)
async def initialize_databases():
    """初始化数据库连接（会话级别）"""
    await init_databases()
    yield
    await close_databases()


@pytest_asyncio.fixture
async def mysql_session() -> AsyncSession:
    """创建MySQL数据库会话"""
    async for session in get_mysql_session():
        yield session
        await session.rollback()  # 测试后回滚


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """创建异步测试客户端"""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(mysql_session: AsyncSession) -> User:
    """创建测试用户"""
    user = User(
        wechat_openid="test_openid_123",
        school_id=1,
        nickname="测试用户",
        avatar="https://example.com/avatar.jpg",
        student_id="2021001",
        real_name="张三",
        email="zhangsan@university.edu.cn",
        phone="13800138000",
        verified=True,
        credit_score=80,
        points=0,
    )
    mysql_session.add(user)
    await mysql_session.commit()
    await mysql_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user_profile(
    mysql_session: AsyncSession,
    test_user: User,
) -> UserProfile:
    """创建测试用户档案"""
    profile = UserProfile(
        user_id=test_user.id,
        grade="2021级",
        major="计算机科学与技术",
        campus="主校区",
        tags={"tags": ["编程", "算法"]},
        bio="这是一个测试用户",
    )
    mysql_session.add(profile)
    await mysql_session.commit()
    await mysql_session.refresh(profile)
    return profile



@pytest_asyncio.fixture
async def test_user_2(mysql_session: AsyncSession) -> User:
    """创建第二个测试用户"""
    user = User(
        wechat_openid="test_openid_456",
        school_id=1,
        nickname="测试用户2",
        avatar="https://example.com/avatar2.jpg",
        student_id="2021002",
        real_name="李四",
        email="lisi@university.edu.cn",
        phone="13800138001",
        verified=True,
        credit_score=80,
        points=0,
    )
    mysql_session.add(user)
    await mysql_session.commit()
    await mysql_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_school(mysql_session: AsyncSession):
    """创建测试学校"""
    from app.models.course import School, SchoolStatus
    
    school = School(
        name="测试大学",
        short_name="测试大学",
        province="北京市",
        city="北京市",
        status=SchoolStatus.ACTIVE,
    )
    mysql_session.add(school)
    await mysql_session.commit()
    await mysql_session.refresh(school)
    return school


# Alias for db_session to match test expectations
@pytest_asyncio.fixture
async def db_session(mysql_session: AsyncSession) -> AsyncSession:
    """数据库会话别名"""
    return mysql_session
