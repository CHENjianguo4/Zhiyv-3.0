"""评分体系仓储层

提供评分相关的数据访问操作
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating.rating import RatingSubject, Rating, SubjectType


class RatingRepository:
    """评分仓储类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_subject(self, subject: RatingSubject) -> RatingSubject:
        """创建评分主体"""
        self.session.add(subject)
        await self.session.flush()
        await self.session.refresh(subject)
        return subject

    async def get_subject(self, subject_id: int) -> Optional[RatingSubject]:
        """获取主体详情"""
        query = select(RatingSubject).where(RatingSubject.id == subject_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_subjects(
        self,
        school_id: int,
        type: Optional[SubjectType] = None,
        keyword: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
        sort_by: str = "rating_score"
    ) -> List[RatingSubject]:
        """获取主体列表"""
        query = select(RatingSubject).where(RatingSubject.school_id == school_id)
        
        if type:
            query = query.where(RatingSubject.type == type)
        if keyword:
            query = query.where(RatingSubject.name.contains(keyword))
            
        if sort_by == "rating_score":
            query = query.order_by(RatingSubject.rating_score.desc())
        elif sort_by == "rating_count":
            query = query.order_by(RatingSubject.rating_count.desc())
        else:
            query = query.order_by(RatingSubject.created_at.desc())
            
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_rating(self, rating: Rating) -> Rating:
        """创建评分"""
        self.session.add(rating)
        await self.session.flush()
        await self.session.refresh(rating)
        return rating

    async def get_user_rating(self, user_id: int, subject_id: int) -> Optional[Rating]:
        """获取用户对某主体的评分"""
        query = select(Rating).where(
            Rating.user_id == user_id,
            Rating.subject_id == subject_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_ratings(
        self,
        subject_id: int,
        offset: int = 0,
        limit: int = 20
    ) -> List[Rating]:
        """获取主体的评价列表"""
        query = select(Rating).where(
            Rating.subject_id == subject_id
        ).order_by(Rating.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_subject_stats(self, subject_id: int):
        """更新主体评分统计"""
        # 计算平均分和总人数
        stats_query = select(
            func.avg(Rating.score).label("avg_score"),
            func.count(Rating.id).label("count")
        ).where(Rating.subject_id == subject_id)
        
        result = await self.session.execute(stats_query)
        stats = result.one()
        
        avg_score = float(stats.avg_score) if stats.avg_score else 0.0
        count = stats.count if stats.count else 0
        
        # 更新主体表
        subject = await self.get_subject(subject_id)
        if subject:
            subject.rating_score = round(avg_score, 1)
            subject.rating_count = count
            self.session.add(subject)
