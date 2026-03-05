"""搭子组队仓储层

提供搭子相关的数据访问操作
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruitment.recruitment import (
    Recruitment,
    Application,
    RecruitmentStatus,
    ApplicationStatus,
)


class RecruitmentRepository:
    """搭子仓储类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_recruitment(self, recruitment: Recruitment) -> Recruitment:
        """创建招募"""
        self.session.add(recruitment)
        await self.session.flush()
        await self.session.refresh(recruitment)
        return recruitment

    async def get_recruitment(self, recruitment_id: int) -> Optional[Recruitment]:
        """获取招募详情"""
        query = select(Recruitment).where(Recruitment.id == recruitment_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_recruitments(
        self,
        school_id: int,
        status: Optional[RecruitmentStatus] = None,
        offset: int = 0,
        limit: int = 20
    ) -> List[Recruitment]:
        """获取招募列表"""
        query = select(Recruitment).where(Recruitment.school_id == school_id)
        
        if status:
            query = query.where(Recruitment.status == status)
        else:
            # 默认只显示开放的
            query = query.where(Recruitment.status == RecruitmentStatus.OPEN)
            
        query = query.order_by(Recruitment.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_recruitment(self, recruitment: Recruitment) -> Recruitment:
        """更新招募信息"""
        self.session.add(recruitment)
        return recruitment

    async def create_application(self, application: Application) -> Application:
        """创建申请"""
        self.session.add(application)
        await self.session.flush()
        await self.session.refresh(application)
        return application

    async def get_application(self, application_id: int) -> Optional[Application]:
        """获取申请详情"""
        query = select(Application).where(Application.id == application_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_applications(
        self,
        recruitment_id: int,
        status: Optional[ApplicationStatus] = None
    ) -> List[Application]:
        """获取申请列表"""
        query = select(Application).where(Application.recruitment_id == recruitment_id)
        if status:
            query = query.where(Application.status == status)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_application(self, application: Application) -> Application:
        """更新申请状态"""
        self.session.add(application)
        return application
