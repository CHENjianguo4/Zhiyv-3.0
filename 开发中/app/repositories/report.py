"""
Report Repository

Handles database operations for reports.
"""
from typing import List, Optional
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportTargetType, ReportStatus


class ReportRepository:
    """Repository for report database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        reporter_id: int,
        target_type: ReportTargetType,
        target_id: int,
        reason: str,
        description: Optional[str] = None,
        evidence: Optional[dict] = None
    ) -> Report:
        """Create a new report"""
        report = Report(
            reporter_id=reporter_id,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            description=description,
            evidence=evidence,
            status=ReportStatus.PENDING
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_by_id(self, report_id: int) -> Optional[Report]:
        """Get report by ID"""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        status: Optional[ReportStatus] = None,
        target_type: Optional[ReportTargetType] = None,
        reporter_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Report]:
        """Get all reports with optional filters"""
        query = select(Report)
        
        conditions = []
        if status:
            conditions.append(Report.status == status)
        if target_type:
            conditions.append(Report.target_type == target_type)
        if reporter_id:
            conditions.append(Report.reporter_id == reporter_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(Report.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        report_id: int,
        status: ReportStatus,
        handler_id: Optional[int] = None,
        handle_result: Optional[str] = None
    ) -> Optional[Report]:
        """Update report status"""
        report = await self.get_by_id(report_id)
        if not report:
            return None
        
        report.status = status
        if handler_id is not None:
            report.handler_id = handler_id
        if handle_result is not None:
            report.handle_result = handle_result
        
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def count_by_target(
        self,
        target_type: ReportTargetType,
        target_id: int
    ) -> int:
        """Count reports for a specific target"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(Report).where(
                and_(
                    Report.target_type == target_type,
                    Report.target_id == target_id
                )
            )
        )
        return result.scalar_one()

    async def get_pending_count(self) -> int:
        """Get count of pending reports"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(Report).where(
                Report.status == ReportStatus.PENDING
            )
        )
        return result.scalar_one()
