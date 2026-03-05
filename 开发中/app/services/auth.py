"""认证服务

提供用户注册、登录、Token刷新等认证相关功能
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.wechat import WeChatOAuthService

logger = get_logger(__name__)


class AuthService:
    """认证服务类
    
    处理用户认证相关的业务逻辑
    """
    
    def __init__(
        self,
        session: AsyncSession,
        wechat_service: Optional[WeChatOAuthService] = None,
    ):
        """初始化认证服务
        
        Args:
            session: 数据库会话
            wechat_service: 微信OAuth服务实例
        """
        self.session = session
        self.user_repo = UserRepository(session)
        self.wechat_service = wechat_service or WeChatOAuthService()
    
    async def wechat_login(
        self,
        code: str,
        nickname: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> dict:
        """微信授权登录
        
        通过微信code获取openid，如果用户不存在则自动创建账号
        
        Args:
            code: 微信登录凭证code
            nickname: 用户昵称（可选）
            avatar: 用户头像URL（可选）
            
        Returns:
            包含access_token、refresh_token和用户信息的字典
            
        Raises:
            BusinessException: 当微信授权失败时
        """
        # 1. 通过code换取openid
        logger.info("开始微信授权登录", code=code[:10] + "...")
        
        wechat_data = await self.wechat_service.code2session(code)
        openid = wechat_data["openid"]
        unionid = wechat_data.get("unionid")
        
        logger.info(
            "获取微信openid成功",
            openid=openid,
            has_unionid=unionid is not None,
        )
        
        # 2. 查找或创建用户
        user = await self.user_repo.get_by_openid(openid)
        
        if user is None:
            # 首次登录，创建新用户
            logger.info("首次登录，创建新用户", openid=openid)
            
            user = await self.user_repo.create(
                wechat_openid=openid,
                wechat_unionid=unionid,
                nickname=nickname or f"用户{openid[:8]}",
                avatar=avatar,
            )
            
            logger.info(
                "用户创建成功",
                user_id=user.id,
                openid=openid,
            )
        else:
            # 已存在用户，更新昵称和头像（如果提供）
            if nickname or avatar:
                update_data = {}
                if nickname:
                    update_data["nickname"] = nickname
                if avatar:
                    update_data["avatar"] = avatar
                
                user = await self.user_repo.update(user.id, **update_data)
                logger.info(
                    "更新用户信息",
                    user_id=user.id,
                    updated_fields=list(update_data.keys()),
                )
        
        # 3. 生成JWT tokens
        token_data = {
            "sub": str(user.id),
            "openid": openid,
            "role": user.role.value,
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(
            "微信登录成功",
            user_id=user.id,
            role=user.role.value,
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "nickname": user.nickname,
                "avatar": user.avatar,
                "role": user.role.value,
                "verified": user.verified,
                "credit_score": user.credit_score,
                "status": user.status.value,
            },
        }
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """刷新访问令牌
        
        使用refresh token获取新的access token
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            包含新access_token的字典
            
        Raises:
            BusinessException: 当refresh token无效或用户不存在时
        """
        # 1. 验证refresh token
        try:
            payload = verify_refresh_token(refresh_token)
        except Exception as e:
            logger.warning("刷新令牌验证失败", error=str(e))
            raise BusinessException(
                message="无效的刷新令牌",
                error_code="INVALID_REFRESH_TOKEN",
            ) from e
        
        user_id = int(payload["sub"])
        
        # 2. 验证用户是否存在且状态正常
        user = await self.user_repo.get_by_id(user_id)
        
        if user is None:
            logger.warning("刷新令牌对应的用户不存在", user_id=user_id)
            raise BusinessException(
                message="用户不存在",
                error_code="USER_NOT_FOUND",
            )
        
        if user.status.value != "active":
            logger.warning(
                "用户状态异常",
                user_id=user_id,
                status=user.status.value,
            )
            raise BusinessException(
                message="用户账号已被禁用",
                error_code="USER_ACCOUNT_DISABLED",
            )
        
        # 3. 生成新的access token
        token_data = {
            "sub": str(user.id),
            "openid": user.wechat_openid,
            "role": user.role.value,
        }
        
        new_access_token = create_access_token(token_data)
        
        logger.info("刷新访问令牌成功", user_id=user.id)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }
    
    async def get_current_user(self, user_id: int) -> User:
        """获取当前登录用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象
            
        Raises:
            BusinessException: 当用户不存在或状态异常时
        """
        user = await self.user_repo.get_by_id(user_id)
        
        if user is None:
            logger.warning("用户不存在", user_id=user_id)
            raise BusinessException(
                message="用户不存在",
                error_code="USER_NOT_FOUND",
            )
        
        if user.status.value != "active":
            logger.warning(
                "用户状态异常",
                user_id=user_id,
                status=user.status.value,
            )
            raise BusinessException(
                message="用户账号已被禁用",
                error_code="USER_ACCOUNT_DISABLED",
            )
        
        return user


def get_auth_service(session: AsyncSession) -> AuthService:
    """获取认证服务实例
    
    Args:
        session: 数据库会话
        
    Returns:
        AuthService实例
    """
    return AuthService(session)
