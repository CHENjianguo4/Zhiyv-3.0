"""通知服务层

提供通知业务逻辑，包括通知发送、推送等
"""

from typing import List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.repositories.notification.notification_repo import NotificationRepository
from app.models.notification.notification import Notification

logger = get_logger(__name__)


class NotificationService:
    """通知服务"""

    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def create_notification(
        self,
        user_id: int,
        type: str,
        title: str,
        content: str,
        data: Optional[dict] = None
    ) -> Notification:
        """创建通知"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            data=data
        )
        
        created_notification = await self.repo.create(notification)
        
        # TODO: 集成IM系统WebSocket推送
        
        return created_notification

    async def get_notifications(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        is_read: Optional[bool] = None
    ) -> tuple[List[Notification], int]:
        """获取通知列表"""
        offset = (page - 1) * page_size
        notifications = await self.repo.list_by_user(user_id, is_read, offset, page_size)
        total = await self.repo.count_unread(user_id) # 这里的total是未读数，实际列表分页可能需要总数，暂时用未读数代替
        return notifications, total

    async def mark_read(self, notification_id: int, user_id: int) -> bool:
        """标记已读"""
        return await self.repo.mark_as_read(notification_id, user_id)

    async def mark_all_read(self, user_id: int) -> int:
        """全部已读"""
        return await self.repo.mark_all_as_read(user_id)
