"""积分体系API接口"""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.points.points_service import PointsService
from app.repositories.user import UserRepository
from app.schemas.user import PointLogDTO
from app.core.response import success_response, error_response

router = APIRouter()

# 依赖注入
async def get_points_service(
    db: AsyncSession = Depends(get_db),
) -> PointsService:
    repo = UserRepository(db)
    return PointsService(repo)


@router.get("/points/balance", response_model=dict)
async def get_balance(
    current_user: User = Depends(get_current_user),
    service: PointsService = Depends(get_points_service),
):
    """获取当前积分余额"""
    points = await service.get_user_points(current_user.id)
    return success_response(data={"points": points})


@router.get("/points/history", response_model=dict)
async def get_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: PointsService = Depends(get_points_service),
):
    """获取积分变更历史"""
    logs = await service.get_point_history(current_user.id, page, page_size)
    return success_response(
        data=[PointLogDTO.from_orm(log).model_dump() for log in logs]
    )


@router.get("/points/ranking", response_model=dict)
async def get_ranking(
    limit: int = 10,
    service: PointsService = Depends(get_points_service),
):
    """获取积分排行榜（Top N）"""
    # TODO: 实现排行榜查询逻辑（建议基于Redis ZSET）
    return success_response(data=[], message="排行榜功能开发中")
