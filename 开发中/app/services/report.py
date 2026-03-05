"""
Report Service

Business logic for report management.
"""
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.report import Report, ReportTargetType, ReportStatus
from app.repositories.report import ReportRepository
from app.core.exceptions import ValidationError, NotFoundError, PermissionDeniedError


class ReportService:
    """Service for report management"""
    
    # Maximum reports per user per day
    MAX_REPORTS_PER_DAY = 10
    
    # Minimum time between reports (seconds)
    MIN_REPORT_INTERVAL = 60

    def __init__(self, repository: ReportRepository):
        self.repository = repository

    async def submit_report(
        self,
        reporter_id: int,
        target_type: ReportTargetType,
        target_id: int,
        reason: str,
        description: Optional[str] = None,
        evidence: Optional[dict] = None
    ) -> Report:
        """Submit a new report"""
        # Validate reason
        if not reason or len(reason.strip()) == 0:
            raise ValidationError("举报原因不能为空")
        
        # Check if user has exceeded daily limit
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_reports = await self.repository.get_all(
            reporter_id=reporter_id,
            limit=self.MAX_REPORTS_PER_DAY + 1
        )
        
        # Filter reports from today
        today_count = sum(
            1 for r in today_reports
            if r.created_at >= today_start
        )
        
        if today_count >= self.MAX_REPORTS_PER_DAY:
            raise ValidationError(f"每日举报次数已达上限（{self.MAX_REPORTS_PER_DAY}次）")
        
        # Create report
        report = await self.repository.create(
            reporter_id=reporter_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            description=description,
            evidence=evidence
        )
        
        return report

    async def get_report(self, report_id: int) -> Report:
        """Get report by ID"""
        report = await self.repository.get_by_id(report_id)
        if not report:
            raise NotFoundError(f"举报记录 ID {report_id} 不存在")
        return report

    async def get_reports(
        self,
        status: Optional[ReportStatus] = None,
        target_type: Optional[ReportTargetType] = None,
        reporter_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Report]:
        """Get reports with filters"""
        return await self.repository.get_all(
            status=status,
            target_type=target_type,
            reporter_id=reporter_id,
            limit=limit,
            offset=offset
        )

    async def process_report(
        self,
        report_id: int,
        handler_id: int,
        action: str,
        result: Optional[str] = None
    ) -> Report:
        """
        Process a report
        
        Args:
            report_id: Report ID
            handler_id: Admin user ID
            action: "approve" or "reject"
            result: Processing result description
        """
        report = await self.get_report(report_id)
        
        if report.status != ReportStatus.PENDING:
            raise ValidationError("该举报已被处理")
        
        # Update status
        if action == "approve":
            new_status = ReportStatus.RESOLVED
        elif action == "reject":
            new_status = ReportStatus.REJECTED
        else:
            raise ValidationError("无效的处理动作")
        
        updated_report = await self.repository.update_status(
            report_id=report_id,
            status=new_status,
            handler_id=handler_id,
            handle_result=result
        )
        
        return updated_report

    async def get_target_report_count(
        self,
        target_type: ReportTargetType,
        target_id: int
    ) -> int:
        """Get report count for a specific target"""
        return await self.repository.count_by_target(target_type, target_id)

    async def get_pending_count(self) -> int:
        """Get count of pending reports"""
        return await self.repository.get_pending_count()

    async def get_statistics(self) -> dict:
        """Get report statistics"""
        pending_count = await self.repository.get_pending_count()
        
        # Get all reports for statistics
        all_reports = await self.repository.get_all(limit=10000)
        
        total = len(all_reports)
        resolved = sum(1 for r in all_reports if r.status == ReportStatus.RESOLVED)
        rejected = sum(1 for r in all_reports if r.status == ReportStatus.REJECTED)
        
        # Count by target type
        by_type = {}
        for target_type in ReportTargetType:
            count = sum(1 for r in all_reports if r.target_type == target_type)
            by_type[target_type.value] = count
        
        return {
            "total": total,
            "pending": pending_count,
            "resolved": resolved,
            "rejected": rejected,
            "by_type": by_type
        }
