"""评分体系API接口"""

from typing import List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.rating.rating_service import RatingService
from app.repositories.rating.rating_repo import RatingRepository
from app.models.rating.rating import SubjectType
from app.core.response import success_response, error_response

router = APIRouter()

# 依赖注入
async def get_rating_service(
    db: AsyncSession = Depends(get_db),
) -> RatingService:
    repo = RatingRepository(db)
    return RatingService(repo)


class SubjectCreate(BaseModel):
    name: str = Field(..., max_length=100)
    type: SubjectType
    description: str
    cover_image: Optional[str] = None
    location: Optional[str] = None


class RatingCreate(BaseModel):
    subject_id: int
    score: int = Field(..., ge=1, le=5)
    content: str
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_anonymous: bool = False


@router.post("/subjects", response_model=dict)
async def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(get_current_user),
    service: RatingService = Depends(get_rating_service),
):
    """创建评分主体"""
    subject = await service.create_subject(
        school_id=current_user.school_id,
        creator_id=current_user.id,
        type=data.type,
        name=data.name,
        description=data.description,
        cover_image=data.cover_image,
        location=data.location
    )
    return success_response(data={"id": subject.id}, message="主体创建成功")


@router.post("/ratings", response_model=dict)
async def create_rating(
    data: RatingCreate,
    current_user: User = Depends(get_current_user),
    service: RatingService = Depends(get_rating_service),
):
    """提交评分"""
    rating = await service.create_rating(
        subject_id=data.subject_id,
        user_id=current_user.id,
        score=data.score,
        content=data.content,
        images=data.images,
        tags=data.tags,
        is_anonymous=data.is_anonymous
    )
    return success_response(data={"id": rating.id}, message="评分提交成功")


@router.get("/subjects", response_model=dict)
async def list_subjects(
    type: Optional[SubjectType] = None,
    sort_by: str = Query("rating_score", enum=["rating_score", "rating_count", "created_at"]),
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: RatingService = Depends(get_rating_service),
):
    """获取主体列表"""
    subjects = await service.list_subjects(
        current_user.school_id, type, page, page_size, sort_by
    )
    return success_response(
        data=[
            {
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "score": float(s.rating_score),
                "count": s.rating_count,
                "cover_image": s.cover_image
            } for s in subjects
        ]
    )
