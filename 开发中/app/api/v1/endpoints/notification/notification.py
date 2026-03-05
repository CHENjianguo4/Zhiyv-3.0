"""通知相关API接口"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.notification.notification_service import NotificationService
from app.repositories.notification.notification_repo import NotificationRepository
from app.core.response import success_response, error_response

router = APIRouter()

# 依赖注入
async def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    repo = NotificationRepository(db)
    return NotificationService(repo)


@router.get("/notifications", response_model=dict)
async def list_notifications(
    is_read: Optional[bool] = Query(None, description="是否已读"),
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """获取通知列表"""
    try:
        notifications, unread_count = await service.get_notifications(
            current_user.id, page, page_size, is_read
        )
        
        return success_response(
            data={
                "items": [
                    {
                        "id": n.id,
                        "type": n.type,
                        "title": n.title,
                        "content": n.content,
                        "is_read": n.is_read,
                        "created_at": n.created_at,
                        "data": n.data
                    } for n in notifications
                ],
                "unread_count": unread_count
            },
            message="获取通知列表成功"
        )
    except Exception as e:
        return error_response(message=f"获取通知失败: {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/notifications/{notification_id}/read", response_model=dict)
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """标记单条已读"""
    success = await service.mark_read(notification_id, current_user.id)
    if not success:
        return error_response(message="通知不存在或已读", code=status.HTTP_404_NOT_FOUND)
    return success_response(message="标记已读成功")


@router.post("/notifications/read-all", response_model=dict)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """全部标记已读"""
    count = await service.mark_all_read(current_user.id)
    return success_response(data={"count": count}, message="全部标记已读成功")
