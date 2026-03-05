"""校园身份认证服务

提供校园身份认证相关功能，包括学号、姓名、邮箱验证
"""

import re
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.models.user import User, UserProfile
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class VerificationService:
    """校园身份认证服务类
    
    处理校园身份认证相关的业务逻辑
    """
    
    def __init__(self, session: AsyncSession):
        """初始化认证服务
        
        Args:
            session: 数据库会话
        """
        self.session = session
        self.user_repo = UserRepository(session)
    
    def validate_student_id(self, student_id: str) -> bool:
        """验证学号格式
        
        学号格式要求：
        - 长度为6-20位
        - 只能包含数字和字母
        
        Args:
            student_id: 学号
            
        Returns:
            bool: 格式是否有效
        """
        if not student_id:
            return False
        
        # 检查长度
        if len(student_id) < 6 or len(student_id) > 20:
            return False
        
        # 检查格式：只能包含数字和字母
        pattern = r'^[A-Za-z0-9]+$'
        return bool(re.match(pattern, student_id))
    
    def validate_name(self, name: str) -> bool:
        """验证姓名格式
        
        姓名格式要求：
        - 长度为2-50个字符
        - 只能包含中文、英文字母和空格
        
        Args:
            name: 姓名
            
        Returns:
            bool: 格式是否有效
        """
        if not name:
            return False
        
        # 检查长度
        if len(name) < 2 or len(name) > 50:
            return False
        
        # 检查格式：只能包含中文、英文字母和空格
        pattern = r'^[\u4e00-\u9fa5a-zA-Z\s]+$'
        return bool(re.match(pattern, name))
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式
        
        邮箱格式要求：
        - 符合标准邮箱格式
        - 必须是校园邮箱（.edu.cn结尾）
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 格式是否有效
        """
        if not email:
            return False
        
        # 检查基本邮箱格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False
        
        # 检查是否为校园邮箱（.edu.cn结尾）
        if not email.lower().endswith('.edu.cn'):
            return False
        
        return True
    
    async def verify_identity(
        self,
        user_id: int,
        student_id: str,
        name: str,
        email: str,
    ) -> dict:
        """校园身份认证
        
        验证用户提交的认证信息，通过后更新用户状态并创建用户档案
        
        Args:
            user_id: 用户ID
            student_id: 学号
            name: 姓名
            email: 校园邮箱
            
        Returns:
            dict: 包含认证结果和用户信息的字典
            
        Raises:
            ValidationError: 当认证信息格式无效时
        """
        logger.info(
            "开始校园身份认证",
            user_id=user_id,
            student_id=student_id,
            name=name,
            email=email,
        )
        
        # 1. 验证输入格式
        validation_errors = []
        
        if not self.validate_student_id(student_id):
            validation_errors.append({
                "field": "student_id",
                "message": "学号格式不正确，应为6-20位数字或字母",
            })
        
        if not self.validate_name(name):
            validation_errors.append({
                "field": "name",
                "message": "姓名格式不正确，应为2-50个字符的中文或英文",
            })
        
        if not self.validate_email(email):
            validation_errors.append({
                "field": "email",
                "message": "邮箱格式不正确，必须是校园邮箱（.edu.cn结尾）",
            })
        
        if validation_errors:
            logger.warning(
                "认证信息验证失败",
                user_id=user_id,
                errors=validation_errors,
            )
            raise ValidationError(
                message="认证信息格式不正确",
                details=validation_errors,
            )
        
        # 2. 获取用户
        user = await self.user_repo.get_user_by_id(user_id)
        if user is None:
            logger.error("用户不存在", user_id=user_id)
            raise ValidationError(
                message="用户不存在",
                details=[{"field": "user_id", "message": "用户不存在"}],
            )
        
        # 3. 检查是否已认证
        if user.verified:
            logger.warning("用户已完成认证", user_id=user_id)
            raise ValidationError(
                message="您已完成校园身份认证",
                details=[{"field": "verified", "message": "用户已认证"}],
            )
        
        # 4. 检查学号是否已被使用
        existing_user = await self.user_repo.get_user_by_student_id(
            school_id=user.school_id,
            student_id=student_id,
        )
        if existing_user and existing_user.id != user_id:
            logger.warning(
                "学号已被使用",
                user_id=user_id,
                student_id=student_id,
                existing_user_id=existing_user.id,
            )
            raise ValidationError(
                message="该学号已被其他用户使用",
                details=[{"field": "student_id", "message": "学号已被使用"}],
            )
        
        # 5. 更新用户认证信息
        user.student_id = student_id
        user.real_name = name
        user.email = email
        user.verified = True
        
        await self.user_repo.update_user(user)
        
        logger.info(
            "用户认证信息更新成功",
            user_id=user_id,
            verified=True,
        )
        
        # 6. 创建用户档案（如果不存在）
        profile = await self.user_repo.get_profile_by_user_id(user_id)
        
        if profile is None:
            # 创建新档案
            profile = UserProfile(
                user_id=user_id,
                grade=None,  # 可以从学号推断，暂时留空
                major=None,  # 需要用户后续填写
                campus=None,  # 需要用户后续填写
                tags=None,  # 需要用户后续填写
                bio=None,
                privacy_settings=None,
            )
            await self.user_repo.create_profile(profile)
            
            logger.info(
                "用户档案创建成功",
                user_id=user_id,
            )
        
        # 7. 提交事务
        await self.session.commit()
        
        logger.info(
            "校园身份认证完成",
            user_id=user_id,
            student_id=student_id,
        )
        
        return {
            "verified": True,
            "user_id": user_id,
            "profile": {
                "user_id": profile.user_id,
                "grade": profile.grade,
                "major": profile.major,
                "campus": profile.campus,
            },
        }


def get_verification_service(session: AsyncSession) -> VerificationService:
    """获取认证服务实例
    
    Args:
        session: 数据库会话
        
    Returns:
        VerificationService实例
    """
    return VerificationService(session)
