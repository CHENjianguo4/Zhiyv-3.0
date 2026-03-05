"""权限管理系统测试

测试基于角色和信用分的权限验证功能
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
    InsufficientCreditError,
    UnverifiedUserError,
)
from app.core.permissions import check_permission, require_verified
from app.models.user import User, UserRole, UserStatus
from app.repositories.user import UserRepository


@pytest.fixture
async def verified_user(db_session: AsyncSession) -> User:
    """创建已认证用户"""
    user_repo = UserRepository(db_session)
    user = User(
        wechat_openid="test_verified_user",
        school_id=1,
        nickname="已认证用户",
        avatar="https://example.com/avatar.jpg",
        verified=True,
        credit_score=80,
    )
    user = await user_repo.create_user(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def unverified_user(db_session: AsyncSession) -> User:
    """创建未认证用户"""
    user_repo = UserRepository(db_session)
    user = User(
        wechat_openid="test_unverified_user",
        school_id=1,
        nickname="未认证用户",
        avatar="https://example.com/avatar.jpg",
    )
    user = await user_repo.create_user(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user



@pytest.fixture
async def low_credit_user(db_session: AsyncSession) -> User:
    """创建低信用分用户（信用分50）"""
    user_repo = UserRepository(db_session)
    user = User(
        wechat_openid="test_low_credit_user",
        school_id=1,
        nickname="低信用分用户",
        avatar="https://example.com/avatar.jpg",
        verified=True,
        credit_score=50,
    )
    user = await user_repo.create_user(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def very_low_credit_user(db_session: AsyncSession) -> User:
    """创建极低信用分用户（信用分20）"""
    user_repo = UserRepository(db_session)
    user = User(
        wechat_openid="test_very_low_credit_user",
        school_id=1,
        nickname="极低信用分用户",
        avatar="https://example.com/avatar.jpg",
        verified=True,
        credit_score=20,
    )
    user = await user_repo.create_user(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """创建管理员用户"""
    user_repo = UserRepository(db_session)
    user = User(
        wechat_openid="test_admin_user",
        school_id=1,
        nickname="管理员",
        avatar="https://example.com/avatar.jpg",
        verified=True,
        role=UserRole.ADMIN,
        credit_score=100,
    )
    user = await user_repo.create_user(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


class TestRequireVerified:
    """测试require_verified装饰器"""
    
    async def test_verified_user_passes(self, verified_user: User):
        """已认证用户应该通过验证"""
        from app.core.permissions import require_verified
        
        checker = require_verified()
        result = checker(verified_user)
        assert result == verified_user
    
    async def test_unverified_user_fails(self, unverified_user: User):
        """未认证用户应该抛出异常"""
        from app.core.permissions import require_verified
        
        checker = require_verified()
        with pytest.raises(UnverifiedUserError) as exc_info:
            checker(unverified_user)
        
        assert "需要完成校园身份认证" in str(exc_info.value.message)



class TestCheckPermission:
    """测试check_permission函数"""
    
    async def test_unverified_user_cannot_publish_posts(
        self,
        unverified_user: User,
        db_session: AsyncSession,
    ):
        """未认证用户不能发布帖子"""
        with pytest.raises(UnverifiedUserError):
            await check_permission(unverified_user, "publish_posts", db_session)
    
    async def test_unverified_user_cannot_create_orders(
        self,
        unverified_user: User,
        db_session: AsyncSession,
    ):
        """未认证用户不能创建订单"""
        with pytest.raises(UnverifiedUserError):
            await check_permission(unverified_user, "create_orders", db_session)
    
    async def test_unverified_user_cannot_publish_items(
        self,
        unverified_user: User,
        db_session: AsyncSession,
    ):
        """未认证用户不能发布商品"""
        with pytest.raises(UnverifiedUserError):
            await check_permission(unverified_user, "publish_items", db_session)
    
    async def test_unverified_user_cannot_rate(
        self,
        unverified_user: User,
        db_session: AsyncSession,
    ):
        """未认证用户不能评分"""
        with pytest.raises(UnverifiedUserError):
            await check_permission(unverified_user, "rate", db_session)
    
    async def test_verified_user_with_good_credit_can_publish(
        self,
        verified_user: User,
        db_session: AsyncSession,
    ):
        """已认证且信用分良好的用户可以发布内容"""
        # 不应该抛出异常
        await check_permission(verified_user, "publish_posts", db_session)
        await check_permission(verified_user, "publish_items", db_session)
        await check_permission(verified_user, "create_orders", db_session)
    
    async def test_low_credit_user_cannot_accept_orders(
        self,
        low_credit_user: User,
        db_session: AsyncSession,
    ):
        """信用分低于60的用户不能接单"""
        with pytest.raises(InsufficientCreditError) as exc_info:
            await check_permission(low_credit_user, "accept_orders", db_session)
        
        assert "信用分" in str(exc_info.value.message)

    
    async def test_very_low_credit_user_cannot_publish(
        self,
        very_low_credit_user: User,
        db_session: AsyncSession,
    ):
        """信用分低于30的用户不能发布内容"""
        with pytest.raises(InsufficientCreditError) as exc_info:
            await check_permission(very_low_credit_user, "publish_posts", db_session)
        
        assert "信用分过低" in str(exc_info.value.message)
        assert "低于30分" in str(exc_info.value.message)
    
    async def test_very_low_credit_user_cannot_trade(
        self,
        very_low_credit_user: User,
        db_session: AsyncSession,
    ):
        """信用分低于30的用户不能交易"""
        with pytest.raises(InsufficientCreditError):
            await check_permission(very_low_credit_user, "trade", db_session)
    
    async def test_verified_user_with_high_credit_can_accept_orders(
        self,
        verified_user: User,
        db_session: AsyncSession,
    ):
        """已认证且信用分>=60的用户可以接单"""
        # 不应该抛出异常
        await check_permission(verified_user, "accept_orders", db_session)


class TestCreditScorePermissions:
    """测试基于信用分的权限控制"""
    
    async def test_credit_60_can_accept_orders(
        self,
        db_session: AsyncSession,
    ):
        """信用分60分可以接单"""
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_credit_60",
            school_id=1,
            verified=True,
            credit_score=60,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 不应该抛出异常
        await check_permission(user, "accept_orders", db_session)
    
    async def test_credit_59_cannot_accept_orders(
        self,
        db_session: AsyncSession,
    ):
        """信用分59分不能接单"""
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_credit_59",
            school_id=1,
            verified=True,
            credit_score=59,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        with pytest.raises(InsufficientCreditError):
            await check_permission(user, "accept_orders", db_session)

    
    async def test_credit_30_can_publish(
        self,
        db_session: AsyncSession,
    ):
        """信用分30分可以发布内容"""
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_credit_30",
            school_id=1,
            verified=True,
            credit_score=30,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 不应该抛出异常
        await check_permission(user, "publish_posts", db_session)
        await check_permission(user, "publish_items", db_session)
    
    async def test_credit_29_cannot_publish(
        self,
        db_session: AsyncSession,
    ):
        """信用分29分不能发布内容"""
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_credit_29",
            school_id=1,
            verified=True,
            credit_score=29,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        with pytest.raises(InsufficientCreditError):
            await check_permission(user, "publish_posts", db_session)
        
        with pytest.raises(InsufficientCreditError):
            await check_permission(user, "publish_items", db_session)


class TestRolePermissions:
    """测试基于角色的权限控制"""
    
    async def test_admin_role_check(self, admin_user: User):
        """测试管理员角色检查"""
        from app.core.permissions import require_role
        
        # 管理员应该通过管理员角色检查
        checker = require_role(UserRole.ADMIN)
        result = checker(admin_user)
        assert result == admin_user
    
    async def test_student_cannot_access_admin_resource(self, verified_user: User):
        """学生不能访问管理员资源"""
        from app.core.permissions import require_role
        
        checker = require_role(UserRole.ADMIN)
        with pytest.raises(AuthorizationError) as exc_info:
            checker(verified_user)
        
        assert "需要以下角色" in str(exc_info.value.message)
    
    async def test_multiple_roles_check(self, verified_user: User, admin_user: User):
        """测试多角色检查"""
        from app.core.permissions import require_role
        
        # 允许学生或管理员
        checker = require_role(UserRole.STUDENT, UserRole.ADMIN)
        
        # 学生应该通过
        result1 = checker(verified_user)
        assert result1 == verified_user
        
        # 管理员也应该通过
        result2 = checker(admin_user)
        assert result2 == admin_user
