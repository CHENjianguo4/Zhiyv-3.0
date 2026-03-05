"""营销工具API接口"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.marketing.marketing_service import MarketingService
from app.repositories.marketing.marketing_repo import MarketingRepository
from app.models.marketing.activity import ActivityType
from app.core.response import success_response, error_response

router = APIRouter()

# 依赖注入
async def get_marketing_service(
    db: AsyncSession = Depends(get_db),
) -> MarketingService:
    repo = MarketingRepository(db)
    return MarketingService(repo)


class ActivityCreate(BaseModel):
    title: str
    type: ActivityType
    description: str
    start_time: datetime
    end_time: datetime
    rules: Optional[dict] = None
    rewards: Optional[dict] = None


@router.post("/activities", response_model=dict)
async def create_activity(
    data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    service: MarketingService = Depends(get_marketing_service),
):
    """创建活动（管理员）"""
    # TODO: 权限验证
    activity = await service.create_activity(
        title=data.title,
        type=data.type,
        description=data.description,
        start_time=data.start_time,
        end_time=data.end_time,
        rules=data.rules,
        rewards=data.rewards
    )
    return success_response(data={"id": activity.id}, message="活动创建成功")


@router.get("/activities", response_model=dict)
async def list_activities(
    service: MarketingService = Depends(get_marketing_service),
):
    """获取活动列表"""
    activities = await service.list_activities()
    return success_response(
        data=[
            {
                "id": a.id,
                "title": a.title,
                "type": a.type,
                "start_time": a.start_time,
                "end_time": a.end_time
            } for a in activities
        ]
    )


@router.get("/coupons", response_model=dict)
async def list_coupons(
    is_used: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    service: MarketingService = Depends(get_marketing_service),
):
    """获取我的优惠券"""
    coupons = await service.list_my_coupons(current_user.id, is_used)
    return success_response(
        data=[
            {
                "id": c.id,
                "name": c.name,
                "amount": float(c.amount),
                "min_spend": float(c.min_spend),
                "expire_time": c.expire_time,
                "is_used": c.is_used
            } for c in coupons
        ]
    )
