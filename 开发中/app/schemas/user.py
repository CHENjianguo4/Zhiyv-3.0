"""用户相关的Pydantic模型

定义API请求和响应的数据模型，包含脱敏逻辑
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import UserRole, UserStatus
from app.utils.masking import (
    mask_email,
    mask_phone,
    mask_real_name,
    mask_student_id,
)


# ==================== 请求模型 ====================


class WechatLoginRequest(BaseModel):
    """微信登录请求"""

    code: str = Field(..., description="微信授权code")
    school_id: int = Field(..., description="学校ID", gt=0)


class VerifyIdentityRequest(BaseModel):
    """身份认证请求"""

    student_id: str = Field(..., description="学号", min_length=1, max_length=50)
    real_name: str = Field(..., description="真实姓名", min_length=1, max_length=50)
    email: str = Field(..., description="邮箱", min_length=1, max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """验证邮箱格式"""
        if "@" not in v:
            raise ValueError("邮箱格式不正确")
        return v


class UpdateProfileRequest(BaseModel):
    """更新用户档案请求"""

    nickname: Optional[str] = Field(None, description="昵称", max_length=50)
    avatar: Optional[str] = Field(None, description="头像URL", max_length=255)
    grade: Optional[str] = Field(None, description="年级", max_length=20)
    major: Optional[str] = Field(None, description="专业", max_length=100)
    campus: Optional[str] = Field(None, description="校区", max_length=50)
    tags: Optional[list[str]] = Field(None, description="兴趣标签")
    bio: Optional[str] = Field(None, description="个人简介", max_length=500)


class ChangeCreditScoreRequest(BaseModel):
    """变更信用分请求"""

    amount: int = Field(..., description="变更金额（正数为增加，负数为减少）", ge=1)
    reason: str = Field(..., description="变更原因", min_length=1, max_length=255)
    related_type: Optional[str] = Field(
        None,
        description="关联对象类型（post/order/rating/violation）",
        max_length=50,
    )
    related_id: Optional[int] = Field(None, description="关联对象ID", gt=0)


class AddTagsRequest(BaseModel):
    """添加兴趣标签请求"""

    tags: list[str] = Field(
        ...,
        description="要添加的标签列表",
        min_length=1,
        max_length=20,
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """验证标签"""
        if not v:
            raise ValueError("标签列表不能为空")
        
        # 验证每个标签长度
        for tag in v:
            if not tag or len(tag) > 20:
                raise ValueError("标签长度必须在1-20个字符之间")
        
        return v


class RemoveTagsRequest(BaseModel):
    """删除兴趣标签请求"""

    tags: list[str] = Field(
        ...,
        description="要删除的标签列表",
        min_length=1,
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """验证标签"""
        if not v:
            raise ValueError("标签列表不能为空")
        
        return v


# ==================== 响应模型 ====================


class UserProfileDTO(BaseModel):
    """用户档案DTO（数据传输对象）
    
    用于API响应，包含脱敏后的用户信息
    """

    model_config = ConfigDict(from_attributes=True)

    # 基本信息
    id: int = Field(..., description="用户ID")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")

    # 学校和身份信息（脱敏）
    school_id: int = Field(..., description="学校ID")
    student_id_masked: Optional[str] = Field(None, description="脱敏后的学号")
    real_name_masked: Optional[str] = Field(None, description="脱敏后的真实姓名")
    email_masked: Optional[str] = Field(None, description="脱敏后的邮箱")
    phone_masked: Optional[str] = Field(None, description="脱敏后的手机号")

    # 角色和状态
    role: UserRole = Field(..., description="用户角色")
    verified: bool = Field(..., description="是否已认证")

    # 信用分和积分
    credit_score: int = Field(..., description="信用分")
    points: int = Field(..., description="积分")

    # 账号状态
    status: UserStatus = Field(..., description="账号状态")

    # 档案信息
    grade: Optional[str] = Field(None, description="年级")
    major: Optional[str] = Field(None, description="专业")
    campus: Optional[str] = Field(None, description="校区")
    tags: Optional[list[str]] = Field(None, description="兴趣标签")
    bio: Optional[str] = Field(None, description="个人简介")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    @classmethod
    def from_user(cls, user: Any, profile: Optional[Any] = None) -> "UserProfileDTO":
        """从User和UserProfile对象创建DTO
        
        Args:
            user: User对象
            profile: UserProfile对象（可选）
            
        Returns:
            UserProfileDTO: 脱敏后的用户档案DTO
        """
        # 应用脱敏逻辑
        data = {
            "id": user.id,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "school_id": user.school_id,
            "student_id_masked": mask_student_id(user.student_id),
            "real_name_masked": mask_real_name(user.real_name),
            "email_masked": mask_email(user.email),
            "phone_masked": mask_phone(user.phone),
            "role": user.role,
            "verified": user.verified,
            "credit_score": user.credit_score,
            "points": user.points,
            "status": user.status,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        # 如果有档案信息，添加档案字段
        if profile:
            # 提取tags列表（如果存储为{"tags": [...]}格式）
            tags_value = None
            if profile.tags:
                if isinstance(profile.tags, dict) and "tags" in profile.tags:
                    tags_value = profile.tags["tags"]
                elif isinstance(profile.tags, list):
                    tags_value = profile.tags
            
            data.update(
                {
                    "grade": profile.grade,
                    "major": profile.major,
                    "campus": profile.campus,
                    "tags": tags_value,
                    "bio": profile.bio,
                }
            )
        else:
            data.update(
                {
                    "grade": None,
                    "major": None,
                    "campus": None,
                    "tags": None,
                    "bio": None,
                }
            )

        return cls(**data)


class UserBasicDTO(BaseModel):
    """用户基本信息DTO
    
    用于列表展示等场景，只包含基本信息
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    school_id: int = Field(..., description="学校ID")
    role: UserRole = Field(..., description="用户角色")
    verified: bool = Field(..., description="是否已认证")
    credit_score: int = Field(..., description="信用分")

    @classmethod
    def from_user(cls, user: Any) -> "UserBasicDTO":
        """从User对象创建DTO
        
        Args:
            user: User对象
            
        Returns:
            UserBasicDTO: 用户基本信息DTO
        """
        return cls(
            id=user.id,
            nickname=user.nickname,
            avatar=user.avatar,
            school_id=user.school_id,
            role=user.role,
            verified=user.verified,
            credit_score=user.credit_score,
        )


class CreditLogDTO(BaseModel):
    """信用分记录DTO"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="用户ID")
    change_amount: int = Field(..., description="变更金额")
    reason: Optional[str] = Field(None, description="变更原因")
    related_type: Optional[str] = Field(None, description="关联对象类型")
    related_id: Optional[int] = Field(None, description="关联对象ID")
    created_at: datetime = Field(..., description="创建时间")


class PointLogDTO(BaseModel):
    """积分记录DTO"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="用户ID")
    change_amount: int = Field(..., description="变更金额")
    action_type: Optional[str] = Field(None, description="动作类型")
    description: Optional[str] = Field(None, description="描述")
    created_at: datetime = Field(..., description="创建时间")


class LoginResponse(BaseModel):
    """登录响应"""

    token: str = Field(..., description="JWT Token")
    user: UserProfileDTO = Field(..., description="用户信息")


class CreditScoreResponse(BaseModel):
    """信用分查询响应"""

    score: int = Field(..., description="当前信用分")
    history: list[CreditLogDTO] = Field(..., description="信用分变更历史")


class PointsResponse(BaseModel):
    """积分查询响应"""

    points: int = Field(..., description="当前积分")
    history: list[PointLogDTO] = Field(..., description="积分变更历史")
