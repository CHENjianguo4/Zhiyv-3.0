"""权限管理系统

提供基于角色和信用分的权限验证装饰器和中间件
"""

from functools import wraps
from typing import TYPE_CHECKING, Callable, Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthorizationError,
    InsufficientCreditError,
    UnverifiedUserError,
)
from app.core.logging import get_logger
from app.models.user import User, UserRole
from app.services.credit import CreditService

if TYPE_CHECKING:
    from app.core.dependencies import get_current_user, get_db_session

logger = get_logger(__name__)


def require_verified() -> Callable:
    """要求用户必须完成校园身份认证
    
    用作FastAPI依赖注入，验证用户是否已完成认证
    
    Returns:
        依赖注入函数
        
    Raises:
        UnverifiedUserError: 当用户未完成认证时
        
    Example:
        ```python
        @router.post("/posts")
        async def create_post(
            user: User = Depends(require_verified()),
            db: AsyncSession = Depends(get_db_session),
        ):
            # 只有已认证用户才能发布帖子
            pass
        ```
    """
    def verified_checker(current_user: User) -> User:
        if not current_user.verified:
            logger.warning(
                "未认证用户尝试访问需要认证的资源",
                user_id=current_user.id,
            )
            raise UnverifiedUserError(
                message="需要完成校园身份认证才能执行此操作",
            )
        
        return current_user
    
    return verified_checker


def require_role(*allowed_roles: UserRole) -> Callable:
    """要求用户具有指定角色
    
    创建一个依赖注入函数，验证用户是否具有指定的角色之一
    
    Args:
        *allowed_roles: 允许的角色列表
        
    Returns:
        依赖注入函数
        
    Raises:
        AuthorizationError: 当用户角色不在允许列表中时
        
    Example:
        ```python
        @router.post("/admin/users")
        async def manage_users(
            user: User = Depends(require_role(UserRole.ADMIN)),
        ):
            # 只有管理员才能管理用户
            pass
        ```
    """
    def role_checker(current_user: User) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                "用户角色不足",
                user_id=current_user.id,
                user_role=current_user.role,
                required_roles=[role.value for role in allowed_roles],
            )
            raise AuthorizationError(
                message=f"需要以下角色之一: {', '.join(role.value for role in allowed_roles)}",
            )
        
        return current_user
    
    return role_checker


def require_credit(min_score: int, action: str) -> Callable:
    """要求用户信用分达到最低要求
    
    创建一个依赖注入函数，验证用户信用分是否满足要求
    
    Args:
        min_score: 最低信用分要求
        action: 操作类型（用于日志和错误提示）
        
    Returns:
        依赖注入函数
        
    Raises:
        InsufficientCreditError: 当用户信用分不足时
        
    Example:
        ```python
        @router.post("/orders/accept")
        async def accept_order(
            user: User = Depends(require_credit(60, "接单")),
            db: AsyncSession = Depends(get_db_session),
        ):
            # 只有信用分>=60的用户才能接单
            pass
        ```
    """
    async def credit_checker(
        current_user: User,
        session: AsyncSession,
    ) -> User:
        if current_user.credit_score < min_score:
            logger.warning(
                "用户信用分不足",
                user_id=current_user.id,
                credit_score=current_user.credit_score,
                required_score=min_score,
                action=action,
            )
            
            # 根据信用分给出不同的提示
            if current_user.credit_score < 30:
                message = f"您的信用分过低（{current_user.credit_score}分，低于30分），已被禁止使用交易和发布功能"
            elif current_user.credit_score < 60:
                message = f"您的信用分较低（{current_user.credit_score}分，低于60分），已被限制{action}权限"
            else:
                message = f"您的信用分不足（{current_user.credit_score}分，需要{min_score}分），无法{action}"
            
            raise InsufficientCreditError(message=message)
        
        return current_user
    
    return credit_checker


async def check_permission(
    user: User,
    action: str,
    session: AsyncSession,
) -> None:
    """检查用户是否有权限执行指定操作
    
    综合检查用户的认证状态、角色和信用分
    
    Args:
        user: 用户对象
        action: 操作类型（accept_orders/publish_posts/publish_items/create_orders/rate/trade）
        session: 数据库会话
        
    Raises:
        UnverifiedUserError: 当用户未完成认证时
        InsufficientCreditError: 当用户信用分不足时
        
    Example:
        ```python
        @router.post("/posts")
        async def create_post(
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db_session),
        ):
            await check_permission(current_user, "publish_posts", db)
            # 继续处理发布帖子逻辑
        ```
    """
    # 检查是否需要认证
    actions_requiring_verification = [
        "publish_posts",
        "publish_items",
        "create_orders",
        "accept_orders",
        "rate",
        "trade",
    ]
    
    if action in actions_requiring_verification and not user.verified:
        logger.warning(
            "未认证用户尝试执行需要认证的操作",
            user_id=user.id,
            action=action,
        )
        raise UnverifiedUserError(
            message="需要完成校园身份认证才能执行此操作",
        )
    
    # 检查信用分权限
    credit_service = CreditService(session)
    await credit_service.verify_credit_permission(user.id, action)


class PermissionMiddleware:
    """权限验证中间件
    
    在请求处理前验证用户权限
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """处理请求
        
        Args:
            scope: ASGI scope
            receive: ASGI receive
            send: ASGI send
        """
        # 只处理HTTP请求
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # 获取请求路径
        path = scope.get("path", "")
        
        # 记录请求日志
        logger.debug(
            "权限中间件处理请求",
            path=path,
            method=scope.get("method"),
        )
        
        # 继续处理请求
        await self.app(scope, receive, send)


# 权限装饰器工厂函数
def permission_required(
    verified: bool = False,
    roles: Optional[list[UserRole]] = None,
    min_credit: Optional[int] = None,
    action: Optional[str] = None,
):
    """权限装饰器工厂函数
    
    创建一个装饰器，用于验证用户权限
    
    Args:
        verified: 是否需要完成认证
        roles: 允许的角色列表
        min_credit: 最低信用分要求
        action: 操作类型（用于信用分验证）
        
    Returns:
        装饰器函数
        
    Example:
        ```python
        @permission_required(verified=True, min_credit=60, action="接单")
        async def accept_order(user: User, db: AsyncSession):
            # 只有已认证且信用分>=60的用户才能接单
            pass
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取user和session
            user = kwargs.get("user") or kwargs.get("current_user")
            session = kwargs.get("session") or kwargs.get("db")
            
            if not user:
                raise AuthorizationError(message="无法获取用户信息")
            
            # 检查认证状态
            if verified and not user.verified:
                logger.warning(
                    "未认证用户尝试访问需要认证的资源",
                    user_id=user.id,
                )
                raise UnverifiedUserError(
                    message="需要完成校园身份认证才能执行此操作",
                )
            
            # 检查角色
            if roles and user.role not in roles:
                logger.warning(
                    "用户角色不足",
                    user_id=user.id,
                    user_role=user.role,
                    required_roles=[role.value for role in roles],
                )
                raise AuthorizationError(
                    message=f"需要以下角色之一: {', '.join(role.value for role in roles)}",
                )
            
            # 检查信用分
            if min_credit is not None and session:
                if user.credit_score < min_credit:
                    logger.warning(
                        "用户信用分不足",
                        user_id=user.id,
                        credit_score=user.credit_score,
                        required_score=min_credit,
                        action=action or "此操作",
                    )
                    
                    # 根据信用分给出不同的提示
                    if user.credit_score < 30:
                        message = f"您的信用分过低（{user.credit_score}分，低于30分），已被禁止使用交易和发布功能"
                    elif user.credit_score < 60:
                        message = f"您的信用分较低（{user.credit_score}分，低于60分），已被限制{action or '此操作'}权限"
                    else:
                        message = f"您的信用分不足（{user.credit_score}分，需要{min_credit}分），无法{action or '执行此操作'}"
                    
                    raise InsufficientCreditError(message=message)
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
