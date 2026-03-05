"""评分体系服务层

提供评分相关业务逻辑
"""

from typing import List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.repositories.rating.rating_repo import RatingRepository
from app.models.rating.rating import RatingSubject, Rating, SubjectType
from app.core.exceptions import ValidationError, ResourceNotFoundError, PermissionDeniedError

logger = get_logger(__name__)


class RatingService:
    """评分服务类"""

    def __init__(self, repo: RatingRepository):
        self.repo = repo

    async def create_subject(
        self,
        school_id: int,
        creator_id: int,
        type: SubjectType,
        name: str,
        description: str,
        cover_image: Optional[str] = None,
        location: Optional[str] = None
    ) -> RatingSubject:
        """创建评分主体"""
        # TODO: 审核机制（当前默认通过）
        subject = RatingSubject(
            school_id=school_id,
            creator_id=creator_id,
            type=type,
            name=name,
            description=description,
            cover_image=cover_image,
            location=location,
            is_approved=True
        )
        
        created_subject = await self.repo.create_subject(subject)
        logger.info(f"Rating subject created: {created_subject.id} by user {creator_id}")
        return created_subject

    async def create_rating(
        self,
        subject_id: int,
        user_id: int,
        score: int,
        content: str,
        images: Optional[list] = None,
        tags: Optional[list] = None,
        is_anonymous: bool = False
    ) -> Rating:
        """提交评分"""
        # 1. 验证主体是否存在
        subject = await self.repo.get_subject(subject_id)
        if not subject:
            raise ResourceNotFoundError(f"Subject {subject_id} not found")
            
        # 2. 验证是否已评价
        existing_rating = await self.repo.get_user_rating(user_id, subject_id)
        if existing_rating:
            raise ValidationError("You have already rated this subject")
            
        # 3. 创建评分
        rating = Rating(
            subject_id=subject_id,
            user_id=user_id,
            score=score,
            content=content,
            images=images,
            tags=tags,
            is_anonymous=is_anonymous
        )
        
        created_rating = await self.repo.create_rating(rating)
        
        # 4. 更新主体统计数据
        await self.repo.update_subject_stats(subject_id)
        
        logger.info(f"Rating created: {created_rating.id} by user {user_id}")
        return created_rating

    async def list_subjects(
        self,
        school_id: int,
        type: Optional[SubjectType] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "rating_score"
    ) -> List[RatingSubject]:
        """获取主体列表"""
        offset = (page - 1) * page_size
        return await self.repo.list_subjects(school_id, type, None, offset, page_size, sort_by)

    async def list_ratings(
        self,
        subject_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[Rating]:
        """获取评价列表"""
        offset = (page - 1) * page_size
        return await self.repo.list_ratings(subject_id, offset, page_size)
