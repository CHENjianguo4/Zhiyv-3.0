"""搭子组队服务层

提供搭子相关业务逻辑
"""

from typing import List, Optional
from datetime import datetime

from app.core.logging import get_logger
from app.repositories.recruitment.recruitment_repo import RecruitmentRepository
from app.models.recruitment.recruitment import (
    Recruitment,
    Application,
    RecruitmentStatus,
    ApplicationStatus,
)
from app.core.exceptions import ValidationError, ResourceNotFoundError, PermissionDeniedError

logger = get_logger(__name__)


class RecruitmentService:
    """搭子服务类"""

    def __init__(self, repo: RecruitmentRepository):
        self.repo = repo

    async def create_recruitment(
        self,
        publisher_id: int,
        school_id: int,
        title: str,
        description: str,
        target_number: int,
        tags: Optional[str] = None,
        deadline: Optional[datetime] = None
    ) -> Recruitment:
        """创建招募"""
        recruitment = Recruitment(
            publisher_id=publisher_id,
            school_id=school_id,
            title=title,
            description=description,
            target_number=target_number,
            tags=tags,
            deadline=deadline,
            status=RecruitmentStatus.OPEN
        )
        
        created_recruitment = await self.repo.create_recruitment(recruitment)
        logger.info(f"Recruitment created: {created_recruitment.id} by user {publisher_id}")
        return created_recruitment

    async def apply_recruitment(
        self,
        recruitment_id: int,
        applicant_id: int,
        reason: str,
        contact: str
    ) -> Application:
        """申请入队"""
        # 1. 验证招募状态
        recruitment = await self.repo.get_recruitment(recruitment_id)
        if not recruitment:
            raise ResourceNotFoundError(f"Recruitment {recruitment_id} not found")
            
        if recruitment.status != RecruitmentStatus.OPEN:
            raise ValidationError("Recruitment is not open")
            
        if recruitment.publisher_id == applicant_id:
            raise ValidationError("Cannot apply own recruitment")
            
        # 2. 创建申请
        application = Application(
            recruitment_id=recruitment_id,
            applicant_id=applicant_id,
            reason=reason,
            contact=contact,
            status=ApplicationStatus.PENDING
        )
        
        created_application = await self.repo.create_application(application)
        logger.info(f"Application created: {created_application.id} by user {applicant_id}")
        return created_application

    async def process_application(
        self,
        application_id: int,
        publisher_id: int,
        action: str  # approve/reject
    ) -> Application:
        """处理申请"""
        application = await self.repo.get_application(application_id)
        if not application:
            raise ResourceNotFoundError(f"Application {application_id} not found")
            
        recruitment = await self.repo.get_recruitment(application.recruitment_id)
        if recruitment.publisher_id != publisher_id:
            raise PermissionDeniedError("Only publisher can process application")
            
        if action == "approve":
            application.status = ApplicationStatus.APPROVED
            # 更新当前人数
            recruitment.current_number += 1
            if recruitment.current_number >= recruitment.target_number:
                recruitment.status = RecruitmentStatus.FULL
            await self.repo.update_recruitment(recruitment)
        elif action == "reject":
            application.status = ApplicationStatus.REJECTED
        else:
            raise ValidationError("Invalid action")
            
        updated_application = await self.repo.update_application(application)
        return updated_application

    async def list_recruitments(
        self,
        school_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[Recruitment]:
        """获取招募列表"""
        offset = (page - 1) * page_size
        return await self.repo.list_recruitments(school_id, None, offset, page_size)
