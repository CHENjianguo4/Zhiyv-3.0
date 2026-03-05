"""跑腿服务API接口"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.errand.errand_service import ErrandService
from app.repositories.errand.errand_repo import ErrandRepository
from app.core.response import success_response, error_response

router = APIRouter()

# 依赖注入
async def get_errand_service(
    db: AsyncSession = Depends(get_db),
) -> ErrandService:
    repo = ErrandRepository(db)
    return ErrandService(repo)


class ErrandCreate(BaseModel):
    title: str = Field(..., max_length=100)
    description: str
    price: Decimal = Field(..., gt=0)
    delivery_location: str
    pickup_location: Optional[str] = None
    deadline: Optional[datetime] = None
    is_public: bool = True


@router.post("/orders", response_model=dict)
async def create_order(
    data: ErrandCreate,
    current_user: User = Depends(get_current_user),
    service: ErrandService = Depends(get_errand_service),
):
    """发布跑腿订单"""
    order = await service.create_order(
        publisher_id=current_user.id,
        school_id=current_user.school_id,
        title=data.title,
        description=data.description,
        price=data.price,
        delivery_location=data.delivery_location,
        pickup_location=data.pickup_location,
        deadline=data.deadline,
        is_public=data.is_public
    )
    return success_response(data={"id": order.id}, message="订单发布成功")


@router.post("/orders/{order_id}/accept", response_model=dict)
async def accept_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    service: ErrandService = Depends(get_errand_service),
):
    """接单"""
    await service.accept_order(order_id, current_user.id)
    return success_response(message="接单成功")


@router.post("/orders/{order_id}/complete", response_model=dict)
async def complete_order(
    order_id: int,
    code: str = Query(..., min_length=6, max_length=6),
    current_user: User = Depends(get_current_user),
    service: ErrandService = Depends(get_errand_service),
):
    """完成订单（验证码校验）"""
    await service.complete_order(order_id, code, current_user.id)
    return success_response(message="订单完成")


@router.get("/orders/available", response_model=dict)
async def list_available(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: ErrandService = Depends(get_errand_service),
):
    """获取接单大厅列表"""
    orders = await service.list_available_orders(current_user.school_id, page, page_size)
    return success_response(
        data=[
            {
                "id": o.id,
                "title": o.title,
                "price": float(o.price),
                "delivery_location": o.delivery_location,
                "created_at": o.created_at
            } for o in orders
        ]
    )
