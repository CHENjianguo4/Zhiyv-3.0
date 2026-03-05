"""信用分服务测试

测试信用分管理相关功能
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.models.user import User, UserRole, UserStatus
from app.repositories.user import UserRepository
from app.services.credit import CreditService


class TestCreditService:
    """信用分服务测试类"""
    
    @pytest.mark.asyncio
    async def test_get_credit_score_success(
        self,
        db_session: AsyncSession,
    ):
        """测试获取信用分成功"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_1",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 获取信用分
        service = CreditService(db_session)
        score = await service.get_credit_score(user.id)
        
        # 验证结果
        assert score == 80
    
    @pytest.mark.asyncio
    async def test_get_credit_score_user_not_found(
        self,
        db_session: AsyncSession,
    ):
        """测试获取不存在用户的信用分"""
        service = CreditService(db_session)
        
        with pytest.raises(BusinessException) as exc_info:
            await service.get_credit_score(99999)
        
        assert "用户不存在" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_increase_credit_score_success(
        self,
        db_session: AsyncSession,
    ):
        """测试增加信用分成功"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_2",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 增加信用分
        service = CreditService(db_session)
        updated_user, log = await service.increase_credit_score(
            user_id=user.id,
            amount=10,
            reason="完成订单",
            related_type="order",
            related_id=123,
        )
        await db_session.commit()
        
        # 验证结果
        assert updated_user.credit_score == 90
        assert log.user_id == user.id
        assert log.change_amount == 10
        assert log.reason == "完成订单"
        assert log.related_type == "order"
        assert log.related_id == 123
    
    @pytest.mark.asyncio
    async def test_increase_credit_score_max_limit(
        self,
        db_session: AsyncSession,
    ):
        """测试增加信用分达到上限"""
        # 创建测试用户（信用分95）
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_3",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=95,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 增加信用分（超过上限）
        service = CreditService(db_session)
        updated_user, log = await service.increase_credit_score(
            user_id=user.id,
            amount=10,
            reason="完成订单",
        )
        await db_session.commit()
        
        # 验证结果（应该被限制在100）
        assert updated_user.credit_score == 100
        assert log.change_amount == 10
    
    @pytest.mark.asyncio
    async def test_increase_credit_score_invalid_amount(
        self,
        db_session: AsyncSession,
    ):
        """测试增加信用分金额无效"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_4",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 尝试增加负数或零
        service = CreditService(db_session)
        
        with pytest.raises(BusinessException) as exc_info:
            await service.increase_credit_score(
                user_id=user.id,
                amount=0,
                reason="测试",
            )
        
        assert "必须为正数" in exc_info.value.message
        
        with pytest.raises(BusinessException) as exc_info:
            await service.increase_credit_score(
                user_id=user.id,
                amount=-10,
                reason="测试",
            )
        
        assert "必须为正数" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_decrease_credit_score_success(
        self,
        db_session: AsyncSession,
    ):
        """测试扣除信用分成功"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_5",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 扣除信用分
        service = CreditService(db_session)
        updated_user, log = await service.decrease_credit_score(
            user_id=user.id,
            amount=10,
            reason="违规行为",
            related_type="violation",
            related_id=456,
        )
        await db_session.commit()
        
        # 验证结果
        assert updated_user.credit_score == 70
        assert log.user_id == user.id
        assert log.change_amount == -10
        assert log.reason == "违规行为"
        assert log.related_type == "violation"
        assert log.related_id == 456
    
    @pytest.mark.asyncio
    async def test_decrease_credit_score_min_limit(
        self,
        db_session: AsyncSession,
    ):
        """测试扣除信用分达到下限"""
        # 创建测试用户（信用分5）
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_6",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=5,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 扣除信用分（超过下限）
        service = CreditService(db_session)
        updated_user, log = await service.decrease_credit_score(
            user_id=user.id,
            amount=10,
            reason="违规行为",
        )
        await db_session.commit()
        
        # 验证结果（应该被限制在0）
        assert updated_user.credit_score == 0
        assert log.change_amount == -10
    
    @pytest.mark.asyncio
    async def test_get_credit_history_success(
        self,
        db_session: AsyncSession,
    ):
        """测试获取信用分历史成功"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_7",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 创建多条信用分变更记录
        service = CreditService(db_session)
        await service.increase_credit_score(user.id, 10, "完成订单1")
        await service.decrease_credit_score(user.id, 5, "违规1")
        await service.increase_credit_score(user.id, 3, "完成订单2")
        await db_session.commit()
        
        # 获取历史记录
        logs = await service.get_credit_history(user.id, offset=0, limit=10)
        
        # 验证结果（按时间倒序）
        assert len(logs) == 3
        assert logs[0].change_amount == 3  # 最新的记录
        assert logs[1].change_amount == -5
        assert logs[2].change_amount == 10
    
    @pytest.mark.asyncio
    async def test_check_credit_permissions_high_score(
        self,
        db_session: AsyncSession,
    ):
        """测试高信用分用户权限（>=60分）"""
        # 创建测试用户（信用分80）
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_8",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 检查权限
        service = CreditService(db_session)
        permissions = await service.check_credit_permissions(user.id)
        
        # 验证结果（所有权限都应该为True）
        assert permissions["can_accept_orders"] is True
        assert permissions["can_publish_posts"] is True
        assert permissions["can_publish_items"] is True
        assert permissions["can_create_orders"] is True
        assert permissions["can_rate"] is True
        assert permissions["can_trade"] is True
    
    @pytest.mark.asyncio
    async def test_check_credit_permissions_medium_score(
        self,
        db_session: AsyncSession,
    ):
        """测试中等信用分用户权限（30-59分）"""
        # 创建测试用户（信用分50）
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_9",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=50,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 检查权限
        service = CreditService(db_session)
        permissions = await service.check_credit_permissions(user.id)
        
        # 验证结果（接单权限被限制）
        assert permissions["can_accept_orders"] is False  # 低于60分
        assert permissions["can_publish_posts"] is True
        assert permissions["can_publish_items"] is True
        assert permissions["can_create_orders"] is True
        assert permissions["can_rate"] is True
        assert permissions["can_trade"] is True
    
    @pytest.mark.asyncio
    async def test_check_credit_permissions_low_score(
        self,
        db_session: AsyncSession,
    ):
        """测试低信用分用户权限（<30分）"""
        # 创建测试用户（信用分20）
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_10",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=20,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 检查权限
        service = CreditService(db_session)
        permissions = await service.check_credit_permissions(user.id)
        
        # 验证结果（所有交易和发布权限都被禁止）
        assert permissions["can_accept_orders"] is False
        assert permissions["can_publish_posts"] is False  # 低于30分
        assert permissions["can_publish_items"] is False  # 低于30分
        assert permissions["can_create_orders"] is False  # 低于30分
        assert permissions["can_rate"] is False  # 低于30分
        assert permissions["can_trade"] is False  # 低于30分
    
    @pytest.mark.asyncio
    async def test_verify_credit_permission_success(
        self,
        db_session: AsyncSession,
    ):
        """测试验证权限成功"""
        # 创建测试用户（信用分80）
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_11",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 验证权限（应该成功）
        service = CreditService(db_session)
        await service.verify_credit_permission(user.id, "publish_posts")
        await service.verify_credit_permission(user.id, "accept_orders")
        await service.verify_credit_permission(user.id, "trade")
    
    @pytest.mark.asyncio
    async def test_verify_credit_permission_insufficient(
        self,
        db_session: AsyncSession,
    ):
        """测试验证权限不足"""
        # 创建测试用户（信用分20）
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_12",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=20,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 验证权限（应该失败）
        service = CreditService(db_session)
        
        with pytest.raises(BusinessException) as exc_info:
            await service.verify_credit_permission(user.id, "publish_posts")
        
        assert "信用分过低" in exc_info.value.message
        assert "低于30分" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_verify_credit_permission_unknown_action(
        self,
        db_session: AsyncSession,
    ):
        """测试验证未知操作类型"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_credit_13",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 验证未知操作
        service = CreditService(db_session)
        
        with pytest.raises(BusinessException) as exc_info:
            await service.verify_credit_permission(user.id, "unknown_action")
        
        assert "未知的操作类型" in exc_info.value.message
