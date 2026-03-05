"""搭子组队API接口"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.recruitment.recruitment_service import RecruitmentService
from app.repositories.recruitment.recruitment_repo import RecruitmentRepository
from app.core.response import success_response, error_response

router = APIRouter()

# 依赖注入
async def get_recruitment_service(
    db: AsyncSession = Depends(get_db),
) -> RecruitmentService:
    repo = RecruitmentRepository(db)
    return RecruitmentService(repo)


class RecruitmentCreate(BaseModel):
    title: str = Field(..., max_length=100)
    description: str
    target_number: int = Field(..., gt=0)
    tags: Optional[str] = None
    deadline: Optional[datetime] = None


class ApplicationCreate(BaseModel):
    reason: str
    contact: str


@router.post("/recruitments", response_model=dict)
async def create_recruitment(
    data: RecruitmentCreate,
    current_user: User = Depends(get_current_user),
    service: RecruitmentService = Depends(get_recruitment_service),
):
    """发布招募"""
    recruitment = await service.create_recruitment(
        publisher_id=current_user.id,
        school_id=current_user.school_id,
        title=data.title,
        description=data.description,
        target_number=data.target_number,
        tags=data.tags,
        deadline=data.deadline
    )
    return success_response(data={"id": recruitment.id}, message="招募发布成功")


@router.post("/recruitments/{recruitment_id}/apply", response_model=dict)
async def apply_recruitment(
    recruitment_id: int,
    data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    service: RecruitmentService = Depends(get_recruitment_service),
):
    """申请入队"""
    application = await service.apply_recruitment(
        recruitment_id=recruitment_id,
        applicant_id=current_user.id,
        reason=data.reason,
        contact=data.contact
    )
    return success_response(data={"id": application.id}, message="申请提交成功")


@router.post("/applications/{application_id}/process", response_model=dict)
async def process_application(
    application_id: int,
    action: str = Query(..., enum=["approve", "reject"]),
    current_user: User = Depends(get_current_user),
    service: RecruitmentService = Depends(get_recruitment_service),
):
    """处理申请"""
    await service.process_application(
        application_id=application_id,
        publisher_id=current_user.id,
        action=action
    )
    return success_response(message="处理成功")


@router.get("/recruitments", response_model=dict)
async def list_recruitments(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: RecruitmentService = Depends(get_recruitment_service),
):
    """获取招募列表"""
    recruitments = await service.list_recruitments(
        current_user.school_id, page, page_size
    )
    return success_response(
        data=[
            {
                "id": r.id,
                "title": r.title,
                "target": r.target_number,
                "current": r.current_number,
                "tags": r.tags,
                "created_at": r.created_at
            } for r in recruitments
        ]
    )
