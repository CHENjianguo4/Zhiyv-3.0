"""校园身份认证API端点

提供校园身份认证接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_mysql_session
from app.core.dependencies import get_current_user
from app.core.response import success_response
from app.models.user import User
from app.services.verification import get_verification_service

router = APIRouter(prefix="/auth", tags=["认证"])


# ==================== 请求模型 ====================


class VerificationRequest(BaseModel):
    """校园身份认证请求"""
    
    student_id: str = Field(
        ...,
        description="学号",
        min_length=6,
        max_length=20,
        examples=["2021001"],
    )
    name: str = Field(
        ...,
        description="真实姓名",
        min_length=2,
        max_length=50,
        examples=["张三"],
    )
    email: str = Field(
        ...,
        description="校园邮箱",
        max_length=100,
        examples=["zhangsan@university.edu.cn"],
    )


# ==================== 响应模型 ====================


class ProfileInfo(BaseModel):
    """用户档案信息"""
    
    user_id: int = Field(..., description="用户ID")
    grade: Optional[str] = Field(None, description="年级")
    major: Optional[str] = Field(None, description="专业")
    campus: Optional[str] = Field(None, description="校区")


class VerificationResponse(BaseModel):
    """校园身份认证响应"""
    
    verified: bool = Field(..., description="是否认证成功")
    user_id: int = Field(..., description="用户ID")
    profile: ProfileInfo = Field(..., description="用户档案信息")


# ==================== API端点 ====================


@router.post(
    "/verify-identity",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="校园身份认证",
    description="""
    提交校园身份认证信息。
    
    - 需要提供学号、姓名和校园邮箱
    - 认证通过后将标记用户为已认证状态
    - 自动创建用户档案
    - 开通全量功能权限
    
    **验证规则：**
    - 学号：6-20位数字或字母
    - 姓名：2-50个字符的中文或英文
    - 邮箱：必须是校园邮箱（.edu.cn结尾）
    """,
)
async def verify_identity(
    request: VerificationRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_mysql_session),
):
    """校园身份认证
    
    Args:
        request: 认证请求数据
        current_user: 当前登录用户
        session: 数据库会话
        
    Returns:
        认证响应，包含认证结果和用户档案信息
    """
    verification_service = get_verification_service(session)
    
    result = await verification_service.verify_identity(
        user_id=current_user.id,
        student_id=request.student_id,
        name=request.name,
        email=request.email,
    )
    
    return success_response(
        data=result,
        message="校园身份认证成功",
    )
