"""
Report Schemas

Pydantic models for report API requests and responses.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.report import ReportTargetType, ReportStatus


class ReportCreate(BaseModel):
    """Schema for creating a report"""
    target_type: ReportTargetType = Field(..., description="举报对象类型")
    target_id: int = Field(..., gt=0, description="举报对象ID")
    reason: str = Field(..., min_length=1, max_length=255, description="举报原因")
    description: Optional[str] = Field(None, max_length=1000, description="详细描述")
    evidence: Optional[dict] = Field(None, description="证据（截图、链接等）")


class ReportProcess(BaseModel):
    """Schema for processing a report"""
    action: str = Field(..., description="处理动作: approve/reject")
    result: Optional[str] = Field(None, max_length=500, description="处理结果说明")


class ReportResponse(BaseModel):
    """Schema for report response"""
    id: int
    reporter_id: int
    target_type: ReportTargetType
    target_id: int
    reason: str
    description: Optional[str]
    evidence: Optional[dict]
    status: ReportStatus
    handler_id: Optional[int]
    handle_result: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportStatistics(BaseModel):
    """Schema for report statistics"""
    total: int = Field(..., description="总数")
    pending: int = Field(..., description="待处理")
    resolved: int = Field(..., description="已解决")
    rejected: int = Field(..., description="已驳回")
    by_type: dict = Field(..., description="按类型统计")
