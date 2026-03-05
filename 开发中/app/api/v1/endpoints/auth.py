"""认证相关API端点

提供微信登录、Token刷新等认证接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_mysql_session
from app.core.response import success_response
from app.services.auth import get_auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


# ==================== 请求模型 ====================


class WeChatLoginRequest(BaseModel):
    """微信登录请求"""
    
    code: str = Field(
        ...,
        description="微信登录凭证code",
        min_length=1,
        max_length=100,
    )
    nickname: Optional[str] = Field(
        None,
        description="用户昵称",
        max_length=50,
    )
    avatar: Optional[str] = Field(
        None,
        description="用户头像URL",
        max_length=255,
    )


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    
    refresh_token: str = Field(
        ...,
        description="刷新令牌",
        min_length=1,
    )


# ==================== 响应模型 ====================


class UserInfo(BaseModel):
    """用户信息"""
    
    id: int = Field(..., description="用户ID")
    nickname: str = Field(..., description="用户昵称")
    avatar: Optional[str] = Field(None, description="用户头像URL")
    role: str = Field(..., description="用户角色")
    verified: bool = Field(..., description="是否已认证")
    credit_score: int = Field(..., description="信用分")
    status: str = Field(..., description="账号状态")


class LoginResponse(BaseModel):
    """登录响应"""
    
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(..., description="令牌类型")
    user: UserInfo = Field(..., description="用户信息")


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应"""
    
    access_token: str = Field(..., description="新的访问令牌")
    token_type: str = Field(..., description="令牌类型")


# ==================== API端点 ====================


@router.post(
    "/wechat-login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="微信授权登录",
    description="""
    通过微信小程序授权登录系统。
    
    - 首次登录会自动创建用户账号
    - 返回JWT访问令牌和刷新令牌
    - 访问令牌用于后续API调用
    - 刷新令牌用于获取新的访问令牌
    """,
)
async def wechat_login(
    request: WeChatLoginRequest,
    session: AsyncSession = Depends(get_mysql_session),
):
    """微信授权登录
    
    Args:
        request: 登录请求数据
        session: 数据库会话
        
    Returns:
        登录响应，包含tokens和用户信息
    """
    auth_service = get_auth_service(session)
    
    result = await auth_service.wechat_login(
        code=request.code,
        nickname=request.nickname,
        avatar=request.avatar,
    )
    
    return success_response(
        data=result,
        message="登录成功",
    )


@router.post(
    "/refresh-token",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="刷新访问令牌",
    description="""
    使用刷新令牌获取新的访问令牌。
    
    - 当访问令牌过期时使用
    - 刷新令牌有效期更长（默认7天）
    - 返回新的访问令牌
    """,
)
async def refresh_token(
    request: RefreshTokenRequest,
    session: AsyncSession = Depends(get_mysql_session),
):
    """刷新访问令牌
    
    Args:
        request: 刷新令牌请求数据
        session: 数据库会话
        
    Returns:
        新的访问令牌
    """
    auth_service = get_auth_service(session)
    
    result = await auth_service.refresh_access_token(
        refresh_token=request.refresh_token,
    )
    
    return success_response(
        data=result,
        message="令牌刷新成功",
    )
