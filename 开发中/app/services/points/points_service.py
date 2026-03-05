"""积分体系服务层

提供积分规则、自动发放、兑换等业务逻辑
"""

from typing import Optional, List, Dict
from datetime import datetime

from app.core.logging import get_logger
from app.repositories.user import UserRepository
from app.models.user import User, PointLog
from app.core.exceptions import ValidationError, ResourceNotFoundError

logger = get_logger(__name__)


class PointsService:
    """积分服务类"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        
    # 积分规则配置（后续可移至数据库或配置中心）
    RULES = {
        "daily_login": {"points": 5, "limit": 1, "desc": "每日登录"},
        "post_publish": {"points": 10, "limit": 5, "desc": "发布帖子"},
        "post_essence": {"points": 50, "limit": 0, "desc": "帖子加精"},
        "comment_reply": {"points": 2, "limit": 10, "desc": "发表评论"},
        "material_upload": {"points": 20, "limit": 3, "desc": "上传资料"},
        "rating_submit": {"points": 5, "limit": 5, "desc": "提交评分"},
        "recruitment_complete": {"points": 15, "limit": 0, "desc": "完成组队"},
    }

    async def award_points(
        self,
        user_id: int,
        rule_key: str,
        related_id: Optional[int] = None
    ) -> Optional[PointLog]:
        """根据规则奖励积分"""
        rule = self.RULES.get(rule_key)
        if not rule:
            logger.warning(f"Unknown point rule: {rule_key}")
            return None
            
        points = rule["points"]
        desc = rule["desc"]
        
        # TODO: 检查每日上限（需要Redis支持）
        # current_count = await self.redis.get(f"points:{user_id}:{rule_key}:{date}")
        # if rule["limit"] > 0 and current_count >= rule["limit"]:
        #     return None
            
        try:
            _, log = await self.user_repo.update_points(
                user_id=user_id,
                change_amount=points,
                action_type=rule_key,
                description=desc
            )
            logger.info(f"Points awarded: {points} to user {user_id} for {rule_key}")
            return log
        except Exception as e:
            logger.error(f"Failed to award points: {e}")
            return None

    async def exchange_points(
        self,
        user_id: int,
        amount: int,
        item_type: str,
        item_id: str,
        description: str
    ) -> PointLog:
        """消耗积分兑换"""
        try:
            _, log = await self.user_repo.update_points(
                user_id=user_id,
                change_amount=-amount,
                action_type="exchange",
                description=description
            )
            logger.info(f"Points exchanged: {amount} by user {user_id} for {item_type}:{item_id}")
            return log
        except ValueError as e:
            raise ValidationError(str(e))
        except Exception as e:
            logger.error(f"Failed to exchange points: {e}")
            raise ValidationError("积分兑换失败")

    async def get_user_points(self, user_id: int) -> int:
        """获取用户当前积分"""
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")
        return user.points

    async def get_point_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[PointLog]:
        """获取积分历史"""
        offset = (page - 1) * page_size
        return await self.user_repo.get_point_logs_by_user_id(user_id, offset, page_size)
