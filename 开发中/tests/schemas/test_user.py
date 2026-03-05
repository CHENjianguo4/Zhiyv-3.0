"""测试用户相关的Pydantic模型

测试UserProfileDTO的脱敏逻辑和数据转换
"""

from datetime import datetime

import pytest

from app.models.user import User, UserProfile, UserRole, UserStatus
from app.schemas.user import UserBasicDTO, UserProfileDTO


class TestUserProfileDTO:
    """测试UserProfileDTO"""

    def test_from_user_with_masking(self):
        """测试从User对象创建DTO时应用脱敏"""
        # 创建测试用户
        user = User(
            id=1,
            wechat_openid="test_openid",
            nickname="测试用户",
            avatar="https://example.com/avatar.jpg",
            school_id=1,
            student_id="2021001234",
            real_name="张三",
            email="zhangsan@university.edu.cn",
            phone="13812345678",
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=100,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 创建测试档案
        profile = UserProfile(
            user_id=1,
            grade="2021级",
            major="计算机科学与技术",
            campus="主校区",
            tags={"tags": ["编程", "算法"]},
            bio="热爱编程的学生",
        )

        # 转换为DTO
        dto = UserProfileDTO.from_user(user, profile)

        # 验证基本信息
        assert dto.id == 1
        assert dto.nickname == "测试用户"
        assert dto.avatar == "https://example.com/avatar.jpg"
        assert dto.school_id == 1

        # 验证脱敏信息
        assert dto.student_id_masked == "202****234"
        assert dto.real_name_masked == "张*"
        assert dto.email_masked == "z***n@university.edu.cn"
        assert dto.phone_masked == "138****5678"

        # 验证角色和状态
        assert dto.role == UserRole.STUDENT
        assert dto.verified is True
        assert dto.credit_score == 80
        assert dto.points == 100
        assert dto.status == UserStatus.ACTIVE

        # 验证档案信息
        assert dto.grade == "2021级"
        assert dto.major == "计算机科学与技术"
        assert dto.campus == "主校区"
        assert dto.tags == ["编程", "算法"]
        assert dto.bio == "热爱编程的学生"

    def test_from_user_without_profile(self):
        """测试从User对象创建DTO（无档案）"""
        user = User(
            id=1,
            wechat_openid="test_openid",
            nickname="测试用户",
            avatar="https://example.com/avatar.jpg",
            school_id=1,
            student_id="2021001234",
            real_name="张三",
            email="zhangsan@university.edu.cn",
            phone="13812345678",
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=100,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 转换为DTO（无档案）
        dto = UserProfileDTO.from_user(user, None)

        # 验证基本信息
        assert dto.id == 1
        assert dto.nickname == "测试用户"

        # 验证脱敏信息
        assert dto.student_id_masked == "202****234"
        assert dto.real_name_masked == "张*"

        # 验证档案信息为None
        assert dto.grade is None
        assert dto.major is None
        assert dto.campus is None
        assert dto.tags is None
        assert dto.bio is None

    def test_from_user_with_none_privacy_fields(self):
        """测试从User对象创建DTO（隐私字段为None）"""
        user = User(
            id=1,
            wechat_openid="test_openid",
            nickname="测试用户",
            avatar=None,
            school_id=1,
            student_id=None,
            real_name=None,
            email=None,
            phone=None,
            role=UserRole.STUDENT,
            verified=False,
            credit_score=80,
            points=0,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 转换为DTO
        dto = UserProfileDTO.from_user(user, None)

        # 验证脱敏字段为None
        assert dto.student_id_masked is None
        assert dto.real_name_masked is None
        assert dto.email_masked is None
        assert dto.phone_masked is None

    def test_masking_preserves_database_data(self):
        """测试脱敏不影响数据库原始数据"""
        # 创建测试用户
        user = User(
            id=1,
            wechat_openid="test_openid",
            nickname="测试用户",
            avatar="https://example.com/avatar.jpg",
            school_id=1,
            student_id="2021001234",
            real_name="张三",
            email="zhangsan@university.edu.cn",
            phone="13812345678",
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=100,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 转换为DTO
        dto = UserProfileDTO.from_user(user, None)

        # 验证原始User对象的数据未被修改
        assert user.student_id == "2021001234"
        assert user.real_name == "张三"
        assert user.email == "zhangsan@university.edu.cn"
        assert user.phone == "13812345678"

        # 验证DTO包含脱敏数据
        assert dto.student_id_masked == "202****234"
        assert dto.real_name_masked == "张*"
        assert dto.email_masked == "z***n@university.edu.cn"
        assert dto.phone_masked == "138****5678"

    def test_from_user_with_compound_surname(self):
        """测试复姓用户的脱敏"""
        user = User(
            id=1,
            wechat_openid="test_openid",
            nickname="测试用户",
            avatar=None,
            school_id=1,
            student_id="2021001234",
            real_name="欧阳修",
            email="ouyangxiu@university.edu.cn",
            phone="13812345678",
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=0,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 转换为DTO
        dto = UserProfileDTO.from_user(user, None)

        # 验证复姓脱敏
        assert dto.real_name_masked == "欧阳*"


class TestUserBasicDTO:
    """测试UserBasicDTO"""

    def test_from_user(self):
        """测试从User对象创建基本信息DTO"""
        user = User(
            id=1,
            wechat_openid="test_openid",
            nickname="测试用户",
            avatar="https://example.com/avatar.jpg",
            school_id=1,
            student_id="2021001234",
            real_name="张三",
            email="zhangsan@university.edu.cn",
            phone="13812345678",
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=100,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 转换为基本信息DTO
        dto = UserBasicDTO.from_user(user)

        # 验证基本信息
        assert dto.id == 1
        assert dto.nickname == "测试用户"
        assert dto.avatar == "https://example.com/avatar.jpg"
        assert dto.school_id == 1
        assert dto.role == UserRole.STUDENT
        assert dto.verified is True
        assert dto.credit_score == 80

        # 验证不包含隐私信息
        assert not hasattr(dto, "student_id")
        assert not hasattr(dto, "real_name")
        assert not hasattr(dto, "email")
        assert not hasattr(dto, "phone")


class TestMaskingConsistency:
    """测试脱敏的一致性"""

    def test_same_input_produces_same_output(self):
        """测试相同输入产生相同输出"""
        user1 = User(
            id=1,
            wechat_openid="test_openid",
            nickname="测试用户",
            avatar=None,
            school_id=1,
            student_id="2021001234",
            real_name="张三",
            email="zhangsan@university.edu.cn",
            phone="13812345678",
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=0,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        user2 = User(
            id=2,
            wechat_openid="test_openid2",
            nickname="测试用户2",
            avatar=None,
            school_id=1,
            student_id="2021001234",  # 相同学号
            real_name="张三",  # 相同姓名
            email="zhangsan@university.edu.cn",  # 相同邮箱
            phone="13812345678",  # 相同手机号
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=0,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 转换为DTO
        dto1 = UserProfileDTO.from_user(user1, None)
        dto2 = UserProfileDTO.from_user(user2, None)

        # 验证相同的隐私信息产生相同的脱敏结果
        assert dto1.student_id_masked == dto2.student_id_masked
        assert dto1.real_name_masked == dto2.real_name_masked
        assert dto1.email_masked == dto2.email_masked
        assert dto1.phone_masked == dto2.phone_masked

    def test_different_input_produces_different_output(self):
        """测试不同输入产生不同输出"""
        user1 = User(
            id=1,
            wechat_openid="test_openid",
            nickname="测试用户",
            avatar=None,
            school_id=1,
            student_id="2021001234",
            real_name="张三",
            email="zhangsan@university.edu.cn",
            phone="13812345678",
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=0,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        user2 = User(
            id=2,
            wechat_openid="test_openid2",
            nickname="测试用户2",
            avatar=None,
            school_id=1,
            student_id="2021001235",  # 不同学号
            real_name="李四",  # 不同姓名
            email="lisi@university.edu.cn",  # 不同邮箱
            phone="13912345678",  # 不同手机号
            role=UserRole.STUDENT,
            verified=True,
            credit_score=80,
            points=0,
            status=UserStatus.ACTIVE,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        # 转换为DTO
        dto1 = UserProfileDTO.from_user(user1, None)
        dto2 = UserProfileDTO.from_user(user2, None)

        # 验证不同的隐私信息产生不同的脱敏结果
        assert dto1.student_id_masked != dto2.student_id_masked
        assert dto1.real_name_masked != dto2.real_name_masked
        assert dto1.email_masked != dto2.email_masked
        assert dto1.phone_masked != dto2.phone_masked
