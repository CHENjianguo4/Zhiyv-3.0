"""搜索API接口"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.search.search_service import SearchService
from app.core.response import success_response

router = APIRouter()

# 依赖注入
async def get_search_service() -> SearchService:
    return SearchService()


@router.get("/search", response_model=dict)
async def global_search(
    keyword: str = Query(..., min_length=1),
    type: Optional[str] = Query(None, description="搜索类型(post/item/course/user)"),
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: SearchService = Depends(get_search_service),
):
    """全局搜索"""
    result = await service.search_all(keyword, page, page_size, {"type": type})
    return success_response(data=result)


@router.get("/search/suggestions", response_model=dict)
async def get_suggestions(
    keyword: str = Query(..., min_length=1),
    service: SearchService = Depends(get_search_service),
):
    """获取搜索建议"""
    suggestions = await service.get_suggestions(keyword)
    return success_response(data=suggestions)


@router.get("/search/hot", response_model=dict)
async def get_hot_keywords(
    service: SearchService = Depends(get_search_service),
):
    """获取热门搜索词"""
    keywords = await service.get_hot_keywords()
    return success_response(data=keywords)
