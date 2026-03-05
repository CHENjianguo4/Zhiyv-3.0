"""信用分服务

提供信用分管理相关功能，包括信用分变更、查询、历史记录等
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException
from app.core.logging import get_logger
from app.models.user import CreditLog, User
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class CreditService:
    """信用分服务类
    
    处理信用分相关的业务逻辑
    """
    
    def __init__(self, session: AsyncSession):
        """初始化信用分服务
        
        Args:
            session: 数据库会话
        """
        self.session = session
        self.user_repo = UserRepository(session)
    
    async def get_credit_score(self, user_id: int) -> int:
        """获取用户当前信用分
        
        Args:
            user_id: 用户ID
            
        Returns:
            当前信用分
            
        Raises:
            BusinessException: 当用户不存在时
        """
        user = await self.user_repo.get_user_by_id(user_id)
        
        if user is None:
            logger.warning("用户不存在", user_id=user_id)
            raise BusinessException(
                message="用户不存在",
                error_code="USER_NOT_FOUND",
            )
        
        return user.credit_score
    
    async def get_credit_history(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[CreditLog]:
        """获取用户信用分变更历史
        
        Args:
            user_id: 用户ID
            offset: 偏移量
            limit: 限制数量
            
        Returns:
            信用分变更记录列表
            
        Raises:
            BusinessException: 当用户不存在时
        """
        # 验证用户是否存在
        user = await self.user_repo.get_user_by_id(user_id)
        
        if user is None:
            logger.warning("用户不存在", user_id=user_id)
            raise BusinessException(
                message="用户不存在",
                error_code="USER_NOT_FOUND",
            )
        
        # 获取信用分历史记录
        logs = await self.user_repo.get_credit_logs_by_user_id(
            user_id=user_id,
            offset=offset,
            limit=limit,
        )
        
        return logs
    
    async def increase_credit_score(
        self,
        user_id: int,
        amount: int,
        reason: str,
        related_type: Optional[str] = None,
        related_id: Optional[int] = None,
    ) -> tuple[User, CreditLog]:
        """增加用户信用分
        
        Args:
            user_id: 用户ID
            amount: 增加的分数（必须为正数）
            reason: 变更原因
            related_type: 关联对象类型（post/order/rating/violation）
            related_id: 关联对象ID
            
        Returns:
            更新后的用户对象和信用分记录
            
        Raises:
            BusinessException: 当用户不存在或参数无效时
        """
        # 验证参数
        if amount <= 0:
            logger.warning("增加信用分的金额必须为正数", amount=amount)
            raise BusinessException(
                message="增加信用分的金额必须为正数",
                error_code="INVALID_AMOUNT",
            )
        
        # 更新信用分
        try:
            user, log = await self.user_repo.update_credit_score(
                user_id=user_id,
                change_amount=amount,
                reason=reason,
                related_type=related_type,
                related_id=related_id,
            )
            
            logger.info(
                "增加信用分成功",
                user_id=user_id,
                amount=amount,
                new_score=user.credit_score,
                reason=reason,
            )
            
            return user, log
            
        except ValueError as e:
            logger.warning("增加信用分失败", user_id=user_id, error=str(e))
            raise BusinessException(
                message=str(e),
                error_code="UPDATE_CREDIT_FAILED",
            ) from e
    
    async def decrease_credit_score(
        self,
        user_id: int,
        amount: int,
        reason: str,
        related_type: Optional[str] = None,
        related_id: Optional[int] = None,
    ) -> tuple[User, CreditLog]:
        """扣除用户信用分
        
        Args:
            user_id: 用户ID
            amount: 扣除的分数（必须为正数）
            reason: 变更原因
            related_type: 关联对象类型（post/order/rating/violation）
            related_id: 关联对象ID
            
        Returns:
            更新后的用户对象和信用分记录
            
        Raises:
            BusinessException: 当用户不存在或参数无效时
        """
        # 验证参数
        if amount <= 0:
            logger.warning("扣除信用分的金额必须为正数", amount=amount)
            raise BusinessException(
                message="扣除信用分的金额必须为正数",
                error_code="INVALID_AMOUNT",
            )
        
        # 更新信用分（传入负数）
        try:
            user, log = await self.user_repo.update_credit_score(
                user_id=user_id,
                change_amount=-amount,
                reason=reason,
                related_type=related_type,
                related_id=related_id,
            )
            
            logger.info(
                "扣除信用分成功",
                user_id=user_id,
                amount=amount,
                new_score=user.credit_score,
                reason=reason,
            )
            
            return user, log
            
        except ValueError as e:
            logger.warning("扣除信用分失败", user_id=user_id, error=str(e))
            raise BusinessException(
                message=str(e),
                error_code="UPDATE_CREDIT_FAILED",
            ) from e
    
    async def check_credit_permissions(self, user_id: int) -> dict[str, bool]:
        """检查用户基于信用分的权限
        
        根据需求3.3和3.4：
        - 信用分低于60分：限制接单、发布和交易权限
        - 信用分低于30分：禁止所有交易和发布功能
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限字典，包含各项权限的布尔值
            
        Raises:
            BusinessException: 当用户不存在时
        """
        user = await self.user_repo.get_user_by_id(user_id)
        
        if user is None:
            logger.warning("用户不存在", user_id=user_id)
            raise BusinessException(
                message="用户不存在",
                error_code="USER_NOT_FOUND",
            )
        
        credit_score = user.credit_score
        
        # 根据信用分判断权限
        permissions = {
            "can_accept_orders": credit_score >= 60,  # 可以接单
            "can_publish_posts": credit_score >= 30,  # 可以发布帖子
            "can_publish_items": credit_score >= 30,  # 可以发布商品
            "can_create_orders": credit_score >= 30,  # 可以创建订单
            "can_rate": credit_score >= 30,  # 可以评分
            "can_trade": credit_score >= 30,  # 可以交易
        }
        
        logger.debug(
            "检查用户信用分权限",
            user_id=user_id,
            credit_score=credit_score,
            permissions=permissions,
        )
        
        return permissions
    
    async def verify_credit_permission(
        self,
        user_id: int,
        action: str,
    ) -> None:
        """验证用户是否有权限执行某个操作
        
        Args:
            user_id: 用户ID
            action: 操作类型（accept_orders/publish_posts/publish_items/create_orders/rate/trade）
            
        Raises:
            BusinessException: 当用户权限不足时
        """
        permissions = await self.check_credit_permissions(user_id)
        
        permission_key = f"can_{action}"
        
        if permission_key not in permissions:
            logger.warning("未知的操作类型", action=action)
            raise BusinessException(
                message="未知的操作类型",
                error_code="UNKNOWN_ACTION",
            )
        
        if not permissions[permission_key]:
            user = await self.user_repo.get_user_by_id(user_id)
            credit_score = user.credit_score if user else 0
            
            logger.warning(
                "用户信用分不足",
                user_id=user_id,
                credit_score=credit_score,
                action=action,
            )
            
            # 根据信用分给出不同的提示
            if credit_score < 30:
                message = "您的信用分过低（低于30分），已被禁止使用交易和发布功能"
            elif credit_score < 60:
                message = "您的信用分较低（低于60分），已被限制接单、发布和交易权限"
            else:
                message = "您的信用分不足，无法执行此操作"
            
            raise BusinessException(
                message=message,
                error_code="INSUFFICIENT_CREDIT_SCORE",
            )


def get_credit_service(session: AsyncSession) -> CreditService:
    """获取信用分服务实例
    
    Args:
        session: 数据库会话
        
    Returns:
        CreditService实例
    """
    return CreditService(session)
