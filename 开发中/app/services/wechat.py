"""微信OAuth服务

提供微信授权登录相关功能
"""

import httpx
from typing import Optional

from app.core.config import get_settings
from app.core.exceptions import BusinessException
from app.core.logging import get_logger

logger = get_logger(__name__)


class WeChatOAuthService:
    """微信OAuth服务类
    
    处理微信小程序授权登录流程
    """
    
    # 微信API端点
    CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"
    
    def __init__(self):
        """初始化微信OAuth服务"""
        self.settings = get_settings()
        self.app_id = self.settings.wechat_app_id
        self.app_secret = self.settings.wechat_app_secret
        
    async def code2session(self, code: str) -> dict:
        """通过code换取openid和session_key
        
        Args:
            code: 微信登录凭证code
            
        Returns:
            包含openid、session_key、unionid的字典
            
        Raises:
            BusinessException: 当微信API调用失败时
        """
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.CODE2SESSION_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
            # 检查微信API返回的错误
            if "errcode" in data and data["errcode"] != 0:
                error_msg = data.get("errmsg", "未知错误")
                logger.error(
                    "微信code2session失败",
                    errcode=data["errcode"],
                    errmsg=error_msg,
                )
                raise BusinessException(
                    message=f"微信授权失败: {error_msg}",
                    error_code="WECHAT_AUTH_FAILED",
                )
            
            # 验证必需字段
            if "openid" not in data:
                logger.error("微信API返回数据缺少openid", data=data)
                raise BusinessException(
                    message="微信授权返回数据异常",
                    error_code="WECHAT_INVALID_RESPONSE",
                )
            
            logger.info(
                "微信code2session成功",
                openid=data["openid"],
                has_unionid="unionid" in data,
            )
            
            return {
                "openid": data["openid"],
                "session_key": data.get("session_key"),
                "unionid": data.get("unionid"),
            }
            
        except httpx.HTTPError as e:
            logger.error("微信API请求失败", error=str(e))
            raise BusinessException(
                message="微信服务暂时不可用，请稍后重试",
                error_code="WECHAT_SERVICE_UNAVAILABLE",
            ) from e
    
    async def get_user_info(
        self,
        encrypted_data: str,
        iv: str,
        session_key: str,
    ) -> Optional[dict]:
        """解密微信用户信息
        
        Args:
            encrypted_data: 加密的用户数据
            iv: 加密算法的初始向量
            session_key: 会话密钥
            
        Returns:
            解密后的用户信息字典，包含昵称、头像等
            
        Note:
            此功能需要实现微信数据解密算法，暂时返回None
            后续可以使用 cryptography 库实现 AES-128-CBC 解密
        """
        # TODO: 实现微信用户数据解密
        # 需要使用 AES-128-CBC 算法解密
        logger.warning("微信用户信息解密功能尚未实现")
        return None


def get_wechat_service() -> WeChatOAuthService:
    """获取微信OAuth服务实例
    
    Returns:
        WeChatOAuthService实例
    """
    return WeChatOAuthService()
