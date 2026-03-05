"""后台交易管理API

提供管理员对交易订单、资金流水的管理功能
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, UserRole
from app.models.errand.order import ErrandOrder, ErrandStatus
from app.core.response import success_response, error_response

router = APIRouter()

def check_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/orders", response_model=dict)
async def list_orders(
    page: int = 1,
    page_size: int = 20,
    status: Optional[ErrandStatus] = None,
    school_id: Optional[int] = None,
    current_user: User = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取全量订单列表"""
    offset = (page - 1) * page_size
    query = select(ErrandOrder)
    
    if status:
        query = query.where(ErrandOrder.status == status)
    if school_id:
        query = query.where(ErrandOrder.school_id == school_id)
        
    query = query.order_by(ErrandOrder.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return success_response(
        data=[
            {
                "id": o.id,
                "title": o.title,
                "price": float(o.price),
                "status": o.status,
                "publisher_id": o.publisher_id,
                "runner_id": o.runner_id,
                "created_at": o.created_at
            } for o in orders
        ]
    )


@router.get("/statistics", response_model=dict)
async def get_trade_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取交易统计数据"""
    query = select(
        func.count(ErrandOrder.id).label("total_orders"),
        func.sum(ErrandOrder.price).label("total_amount")
    ).where(ErrandOrder.status == ErrandStatus.COMPLETED)
    
    if start_date:
        query = query.where(ErrandOrder.created_at >= start_date)
    if end_date:
        query = query.where(ErrandOrder.created_at <= end_date)
        
    result = await db.execute(query)
    stats = result.one()
    
    return success_response(
        data={
            "total_orders": stats.total_orders or 0,
            "total_amount": float(stats.total_amount) if stats.total_amount else 0.0
        }
    )
