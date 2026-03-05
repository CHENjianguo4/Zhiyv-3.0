"""校园身份认证服务测试

测试校园身份认证相关功能
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.user import User, UserProfile, UserRole, UserStatus
from app.repositories.user import UserRepository
from app.services.verification import VerificationService


class TestVerificationService:
    """校园身份认证服务测试类"""
    
    @pytest.mark.asyncio
    async def test_validate_student_id_valid(self):
        """测试有效学号验证"""
        service = VerificationService(None)  # type: ignore
        
        # 测试有效学号
        assert service.validate_student_id("2021001") is True
        assert service.validate_student_id("202100123456") is True
        assert service.validate_student_id("ABC123") is True
        assert service.validate_student_id("2021ABC") is True
    
    @pytest.mark.asyncio
    async def test_validate_student_id_invalid(self):
        """测试无效学号验证"""
        service = VerificationService(None)  # type: ignore
        
        # 测试无效学号
        assert service.validate_student_id("") is False  # 空字符串
        assert service.validate_student_id("12345") is False  # 太短
        assert service.validate_student_id("123456789012345678901") is False  # 太长
        assert service.validate_student_id("2021-001") is False  # 包含特殊字符
        assert service.validate_student_id("2021 001") is False  # 包含空格
        assert service.validate_student_id("学号2021") is False  # 包含中文
    
    @pytest.mark.asyncio
    async def test_validate_name_valid(self):
        """测试有效姓名验证"""
        service = VerificationService(None)  # type: ignore
        
        # 测试有效姓名
        assert service.validate_name("张三") is True
        assert service.validate_name("李四") is True
        assert service.validate_name("欧阳修") is True
        assert service.validate_name("John Smith") is True
        assert service.validate_name("Mary Jane") is True
        assert service.validate_name("张 三") is True  # 包含空格
    
    @pytest.mark.asyncio
    async def test_validate_name_invalid(self):
        """测试无效姓名验证"""
        service = VerificationService(None)  # type: ignore
        
        # 测试无效姓名
        assert service.validate_name("") is False  # 空字符串
        assert service.validate_name("张") is False  # 太短
        assert service.validate_name("a" * 51) is False  # 太长
        assert service.validate_name("张三123") is False  # 包含数字
        assert service.validate_name("张三@") is False  # 包含特殊字符
    
    @pytest.mark.asyncio
    async def test_validate_email_valid(self):
        """测试有效邮箱验证"""
        service = VerificationService(None)  # type: ignore
        
        # 测试有效邮箱
        assert service.validate_email("zhangsan@university.edu.cn") is True
        assert service.validate_email("lisi@school.edu.cn") is True
        assert service.validate_email("test.user@example.edu.cn") is True
        assert service.validate_email("user+tag@university.edu.cn") is True
    
    @pytest.mark.asyncio
    async def test_validate_email_invalid(self):
        """测试无效邮箱验证"""
        service = VerificationService(None)  # type: ignore
        
        # 测试无效邮箱
        assert service.validate_email("") is False  # 空字符串
        assert service.validate_email("zhangsan") is False  # 缺少@
        assert service.validate_email("zhangsan@") is False  # 缺少域名
        assert service.validate_email("@university.edu.cn") is False  # 缺少用户名
        assert service.validate_email("zhangsan@university") is False  # 缺少顶级域名
        assert service.validate_email("zhangsan@university.com") is False  # 不是.edu.cn
        assert service.validate_email("zhangsan@university.edu") is False  # 不是.edu.cn
        assert service.validate_email("zhangsan@gmail.com") is False  # 不是校园邮箱
    
    @pytest.mark.asyncio
    async def test_verify_identity_success(
        self,
        db_session: AsyncSession,
    ):
        """测试校园身份认证成功"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_123",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=False,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 执行认证
        service = VerificationService(db_session)
        result = await service.verify_identity(
            user_id=user.id,
            student_id="2021001",
            name="张三",
            email="zhangsan@university.edu.cn",
        )
        
        # 验证结果
        assert result["verified"] is True
        assert result["user_id"] == user.id
        assert result["profile"]["user_id"] == user.id
        
        # 验证用户状态已更新
        updated_user = await user_repo.get_user_by_id(user.id)
        assert updated_user is not None
        assert updated_user.verified is True
        assert updated_user.student_id == "2021001"
        assert updated_user.real_name == "张三"
        assert updated_user.email == "zhangsan@university.edu.cn"
        
        # 验证用户档案已创建
        profile = await user_repo.get_profile_by_user_id(user.id)
        assert profile is not None
        assert profile.user_id == user.id
    
    @pytest.mark.asyncio
    async def test_verify_identity_invalid_student_id(
        self,
        db_session: AsyncSession,
    ):
        """测试学号格式无效"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_456",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=False,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 执行认证（学号格式无效）
        service = VerificationService(db_session)
        
        with pytest.raises(ValidationError) as exc_info:
            await service.verify_identity(
                user_id=user.id,
                student_id="123",  # 太短
                name="张三",
                email="zhangsan@university.edu.cn",
            )
        
        # 验证错误信息
        assert "学号格式不正确" in str(exc_info.value.details)
    
    @pytest.mark.asyncio
    async def test_verify_identity_invalid_email(
        self,
        db_session: AsyncSession,
    ):
        """测试邮箱格式无效"""
        # 创建测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_789",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=False,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 执行认证（邮箱格式无效）
        service = VerificationService(db_session)
        
        with pytest.raises(ValidationError) as exc_info:
            await service.verify_identity(
                user_id=user.id,
                student_id="2021001",
                name="张三",
                email="zhangsan@gmail.com",  # 不是校园邮箱
            )
        
        # 验证错误信息
        assert "邮箱格式不正确" in str(exc_info.value.details)
    
    @pytest.mark.asyncio
    async def test_verify_identity_already_verified(
        self,
        db_session: AsyncSession,
    ):
        """测试用户已认证"""
        # 创建已认证的测试用户
        user_repo = UserRepository(db_session)
        user = User(
            wechat_openid="test_openid_abc",
            nickname="测试用户",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,  # 已认证
            student_id="2021001",
            real_name="张三",
            email="zhangsan@university.edu.cn",
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user = await user_repo.create_user(user)
        await db_session.commit()
        
        # 尝试再次认证
        service = VerificationService(db_session)
        
        with pytest.raises(ValidationError) as exc_info:
            await service.verify_identity(
                user_id=user.id,
                student_id="2021002",
                name="李四",
                email="lisi@university.edu.cn",
            )
        
        # 验证错误信息
        assert "已完成校园身份认证" in str(exc_info.value.message)
    
    @pytest.mark.asyncio
    async def test_verify_identity_duplicate_student_id(
        self,
        db_session: AsyncSession,
    ):
        """测试学号已被使用"""
        # 创建第一个用户（已认证）
        user_repo = UserRepository(db_session)
        user1 = User(
            wechat_openid="test_openid_user1",
            nickname="用户1",
            school_id=1,
            role=UserRole.STUDENT,
            verified=True,
            student_id="2021001",
            real_name="张三",
            email="zhangsan@university.edu.cn",
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user1 = await user_repo.create_user(user1)
        
        # 创建第二个用户（未认证）
        user2 = User(
            wechat_openid="test_openid_user2",
            nickname="用户2",
            school_id=1,
            role=UserRole.STUDENT,
            verified=False,
            credit_score=80,
            status=UserStatus.ACTIVE,
        )
        user2 = await user_repo.create_user(user2)
        await db_session.commit()
        
        # 尝试使用已存在的学号认证
        service = VerificationService(db_session)
        
        with pytest.raises(ValidationError) as exc_info:
            await service.verify_identity(
                user_id=user2.id,
                student_id="2021001",  # 已被user1使用
                name="李四",
                email="lisi@university.edu.cn",
            )
        
        # 验证错误信息
        assert "学号已被其他用户使用" in str(exc_info.value.message)
