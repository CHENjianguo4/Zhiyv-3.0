"""营销工具服务层

提供活动参与、优惠券发放等业务逻辑
"""

from typing import List, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.logging import get_logger
from app.repositories.marketing.marketing_repo import MarketingRepository
from app.models.marketing.activity import Activity, Coupon, ActivityType
from app.core.exceptions import ValidationError, ResourceNotFoundError

logger = get_logger(__name__)


class MarketingService:
    """营销服务类"""

    def __init__(self, repo: MarketingRepository):
        self.repo = repo

    async def create_activity(
        self,
        title: str,
        type: ActivityType,
        description: str,
        start_time: datetime,
        end_time: datetime,
        rules: Optional[dict] = None,
        rewards: Optional[dict] = None
    ) -> Activity:
        """创建活动"""
        activity = Activity(
            title=title,
            type=type,
            description=description,
            start_time=start_time,
            end_time=end_time,
            rules=rules,
            rewards=rewards
        )
        
        created_activity = await self.repo.create_activity(activity)
        logger.info(f"Activity created: {created_activity.id} - {title}")
        return created_activity

    async def issue_coupon(
        self,
        user_id: int,
        name: str,
        amount: Decimal,
        expire_days: int = 30,
        min_spend: Decimal = 0,
        activity_id: Optional[int] = None
    ) -> Coupon:
        """发放优惠券"""
        expire_time = datetime.utcnow() + timedelta(days=expire_days)
        
        coupon = Coupon(
            user_id=user_id,
            activity_id=activity_id,
            name=name,
            amount=amount,
            min_spend=min_spend,
            expire_time=expire_time,
            is_used=False
        )
        
        created_coupon = await self.repo.create_coupon(coupon)
        logger.info(f"Coupon issued: {created_coupon.id} to user {user_id}")
        return created_coupon

    async def list_activities(self) -> List[Activity]:
        """获取活动列表"""
        return await self.repo.list_active_activities()

    async def list_my_coupons(self, user_id: int, is_used: Optional[bool] = None) -> List[Coupon]:
        """获取我的优惠券"""
        return await self.repo.list_user_coupons(user_id, is_used)
