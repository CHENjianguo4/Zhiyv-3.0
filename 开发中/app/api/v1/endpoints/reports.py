"""
Reports API Endpoints

Handles report submission and management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_current_user, require_admin
from app.core.response import success_response
from app.repositories.report import ReportRepository
from app.services.report import ReportService
from app.schemas.report import (
    ReportCreate,
    ReportProcess,
    ReportResponse,
    ReportStatistics
)
from app.models.report import ReportTargetType, ReportStatus
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["reports"])


def get_service(db: AsyncSession = Depends(get_db_session)) -> ReportService:
    """Get report service instance"""
    repository = ReportRepository(db)
    return ReportService(repository)


@router.post("", response_model=ReportResponse)
async def submit_report(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_service)
):
    """
    提交举报
    
    用户可以举报违规内容或用户。
    每日举报次数有限制。
    """
    report = await service.submit_report(
        reporter_id=current_user.id,
        target_type=data.target_type,
        target_id=data.target_id,
        reason=data.reason,
        description=data.description,
        evidence=data.evidence
    )
    return success_response(data=report.to_dict(), message="举报提交成功")


@router.get("", response_model=List[ReportResponse])
async def get_reports(
    status: Optional[ReportStatus] = Query(None, description="状态筛选"),
    target_type: Optional[ReportTargetType] = Query(None, description="类型筛选"),
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_service)
):
    """
    获取举报列表
    
    普通用户只能查看自己的举报记录。
    管理员可以查看所有举报。
    """
    from app.models.user import UserRole
    
    # Check if admin
    if current_user.role == UserRole.ADMIN:
        reporter_id = None  # Admin can see all
    else:
        reporter_id = current_user.id  # User can only see their own
    
    reports = await service.get_reports(
        status=status,
        target_type=target_type,
        reporter_id=reporter_id,
        limit=limit,
        offset=offset
    )
    return success_response(data=[r.to_dict() for r in reports])


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_service)
):
    """
    获取举报详情
    
    用户只能查看自己的举报，管理员可以查看所有举报。
    """
    from app.models.user import UserRole
    from app.core.exceptions import PermissionDeniedError
    
    report = await service.get_report(report_id)
    
    # Check permission
    if current_user.role != UserRole.ADMIN and report.reporter_id != current_user.id:
        raise PermissionDeniedError("无权查看此举报")
    
    return success_response(data=report.to_dict())


@router.post("/{report_id}/process", response_model=ReportResponse, dependencies=[Depends(require_admin)])
async def process_report(
    report_id: int,
    data: ReportProcess,
    current_user: User = Depends(require_admin),
    service: ReportService = Depends(get_service)
):
    """
    处理举报
    
    需要管理员权限。
    可以批准或驳回举报。
    """
    report = await service.process_report(
        report_id=report_id,
        handler_id=current_user.id,
        action=data.action,
        result=data.result
    )
    return success_response(data=report.to_dict(), message="举报处理成功")


@router.get("/statistics/summary", response_model=ReportStatistics, dependencies=[Depends(require_admin)])
async def get_statistics(
    service: ReportService = Depends(get_service)
):
    """
    获取举报统计信息
    
    需要管理员权限。
    """
    stats = await service.get_statistics()
    return success_response(data=stats)


@router.get("/target/{target_type}/{target_id}/count")
async def get_target_report_count(
    target_type: ReportTargetType,
    target_id: int,
    service: ReportService = Depends(get_service)
):
    """
    获取特定对象的举报次数
    
    所有用户可查看。
    """
    count = await service.get_target_report_count(target_type, target_id)
    return success_response(data={"count": count})
