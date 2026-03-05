"""行为分析API接口"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query, BackgroundTasks

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.analytics.analytics_service import AnalyticsService
from app.core.response import success_response

router = APIRouter()

# 依赖注入
async def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


class TrackEvent(BaseModel):
    event: str
    properties: Dict[str, Any] = {}


@router.post("/track", response_model=dict)
async def track_event(
    data: TrackEvent,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """上报行为数据"""
    background_tasks.add_task(
        service.track_event,
        user_id=current_user.id,
        event_name=data.event,
        properties=data.properties
    )
    return success_response(message="上报成功")


@router.get("/stats/users", response_model=dict)
async def get_user_stats(
    days: int = Query(7, ge=1, le=90),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """获取用户统计（仅管理员）"""
    # TODO: 权限验证
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    stats = await service.get_user_stats(start_date, end_date)
    return success_response(data=stats)
