"""通知仓储层

提供通知相关的数据访问操作
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification.notification import Notification


class NotificationRepository:
    """通知仓储类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, notification: Notification) -> Notification:
        """创建通知"""
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def get_by_id(self, notification_id: int) -> Optional[Notification]:
        """获取通知详情"""
        query = select(Notification).where(Notification.id == notification_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20
    ) -> List[Notification]:
        """获取用户通知列表"""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if is_read is not None:
            query = query.where(Notification.is_read == is_read)
            
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_unread(self, user_id: int) -> int:
        """统计未读通知数"""
        query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """标记单条已读"""
        query = update(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).values(is_read=True)
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def mark_all_as_read(self, user_id: int) -> int:
        """标记全部已读"""
        query = update(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).values(is_read=True)
        result = await self.session.execute(query)
        return result.rowcount
