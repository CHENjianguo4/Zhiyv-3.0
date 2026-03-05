"""营销工具仓储层

提供活动和优惠券的数据访问
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing.activity import Activity, Coupon, ActivityType


class MarketingRepository:
    """营销仓储类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_activity(self, activity: Activity) -> Activity:
        """创建活动"""
        self.session.add(activity)
        await self.session.flush()
        await self.session.refresh(activity)
        return activity

    async def get_activity(self, activity_id: int) -> Optional[Activity]:
        """获取活动详情"""
        query = select(Activity).where(Activity.id == activity_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_active_activities(self) -> List[Activity]:
        """获取进行中的活动"""
        now = datetime.utcnow()
        query = select(Activity).where(
            Activity.is_active == True,
            Activity.start_time <= now,
            Activity.end_time >= now
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_coupon(self, coupon: Coupon) -> Coupon:
        """创建优惠券"""
        self.session.add(coupon)
        await self.session.flush()
        await self.session.refresh(coupon)
        return coupon

    async def list_user_coupons(
        self,
        user_id: int,
        is_used: Optional[bool] = None
    ) -> List[Coupon]:
        """获取用户优惠券"""
        query = select(Coupon).where(Coupon.user_id == user_id)
        
        if is_used is not None:
            query = query.where(Coupon.is_used == is_used)
            
        # 未使用的按过期时间排序，已使用的按使用时间排序
        if is_used is False:
            query = query.order_by(Coupon.expire_time)
        else:
            query = query.order_by(Coupon.used_at.desc())
            
        result = await self.session.execute(query)
        return list(result.scalars().all())
