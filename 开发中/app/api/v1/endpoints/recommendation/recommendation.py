"""推荐API接口"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.recommendation.recommendation_service import RecommendationService
from app.core.response import success_response

router = APIRouter()

# 依赖注入
async def get_recommendation_service() -> RecommendationService:
    return RecommendationService()


@router.get("/recommend/posts", response_model=dict)
async def recommend_posts(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """获取推荐帖子"""
    post_ids = await service.recommend_posts(current_user.id, page, page_size)
    # TODO: 根据ID查询帖子详情
    return success_response(data=post_ids)


@router.get("/recommend/items", response_model=dict)
async def recommend_items(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """获取推荐商品"""
    item_ids = await service.recommend_items(current_user.id, page, page_size)
    return success_response(data=item_ids)
