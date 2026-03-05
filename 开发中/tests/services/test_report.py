"""
Tests for Report Service
"""
import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from app.services.report import ReportService
from app.models.report import Report, ReportTargetType, ReportStatus
from app.core.exceptions import ValidationError, NotFoundError


@pytest.fixture
def mock_repository():
    """Mock report repository"""
    return AsyncMock()


@pytest.fixture
def service(mock_repository):
    """Create service instance with mocked repository"""
    return ReportService(mock_repository)


@pytest.mark.asyncio
async def test_submit_report_success(service, mock_repository):
    """Test submitting a report successfully"""
    # Arrange
    mock_repository.get_all.return_value = []  # No previous reports
    mock_report = Report(
        id=1,
        reporter_id=1,
        target_type=ReportTargetType.POST,
        target_id=100,
        reason="违规内容",
        status=ReportStatus.PENDING,
        created_at=datetime.now()
    )
    mock_repository.create.return_value = mock_report
    
    # Act
    result = await service.submit_report(
        reporter_id=1,
        target_type=ReportTargetType.POST,
        target_id=100,
        reason="违规内容"
    )
    
    # Assert
    assert result.id == 1
    assert result.reason == "违规内容"
    mock_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_submit_report_empty_reason(service, mock_repository):
    """Test submitting report with empty reason fails"""
    # Act & Assert
    with pytest.raises(ValidationError, match="举报原因不能为空"):
        await service.submit_report(
            reporter_id=1,
            target_type=ReportTargetType.POST,
            target_id=100,
            reason=""
        )


@pytest.mark.asyncio
async def test_submit_report_exceeds_daily_limit(service, mock_repository):
    """Test submitting report when daily limit is exceeded"""
    # Arrange
    # Create 10 reports from today
    today_reports = [
        Report(
            id=i,
            reporter_id=1,
            target_type=ReportTargetType.POST,
            target_id=i,
            reason="test",
            status=ReportStatus.PENDING,
            created_at=datetime.now()
        )
        for i in range(10)
    ]
    mock_repository.get_all.return_value = today_reports
    
    # Act & Assert
    with pytest.raises(ValidationError, match="每日举报次数已达上限"):
        await service.submit_report(
            reporter_id=1,
            target_type=ReportTargetType.POST,
            target_id=100,
            reason="违规内容"
        )


@pytest.mark.asyncio
async def test_get_report_success(service, mock_repository):
    """Test getting a report by ID"""
    # Arrange
    mock_report = Report(
        id=1,
        reporter_id=1,
        target_type=ReportTargetType.USER,
        target_id=50,
        reason="垃圾用户",
        status=ReportStatus.PENDING,
        created_at=datetime.now()
    )
    mock_repository.get_by_id.return_value = mock_report
    
    # Act
    result = await service.get_report(1)
    
    # Assert
    assert result.id == 1
    assert result.reason == "垃圾用户"


@pytest.mark.asyncio
async def test_get_report_not_found(service, mock_repository):
    """Test getting non-existent report raises error"""
    # Arrange
    mock_repository.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(NotFoundError, match="不存在"):
        await service.get_report(999)


@pytest.mark.asyncio
async def test_process_report_approve(service, mock_repository):
    """Test processing report with approve action"""
    # Arrange
    mock_report = Report(
        id=1,
        reporter_id=1,
        target_type=ReportTargetType.POST,
        target_id=100,
        reason="违规",
        status=ReportStatus.PENDING,
        created_at=datetime.now()
    )
    mock_repository.get_by_id.return_value = mock_report
    
    updated_report = Report(
        id=1,
        reporter_id=1,
        target_type=ReportTargetType.POST,
        target_id=100,
        reason="违规",
        status=ReportStatus.RESOLVED,
        handler_id=2,
        handle_result="已处理",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_repository.update_status.return_value = updated_report
    
    # Act
    result = await service.process_report(
        report_id=1,
        handler_id=2,
        action="approve",
        result="已处理"
    )
    
    # Assert
    assert result.status == ReportStatus.RESOLVED
    assert result.handler_id == 2


@pytest.mark.asyncio
async def test_process_report_reject(service, mock_repository):
    """Test processing report with reject action"""
    # Arrange
    mock_report = Report(
        id=1,
        reporter_id=1,
        target_type=ReportTargetType.POST,
        target_id=100,
        reason="违规",
        status=ReportStatus.PENDING,
        created_at=datetime.now()
    )
    mock_repository.get_by_id.return_value = mock_report
    
    updated_report = Report(
        id=1,
        reporter_id=1,
        target_type=ReportTargetType.POST,
        target_id=100,
        reason="违规",
        status=ReportStatus.REJECTED,
        handler_id=2,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_repository.update_status.return_value = updated_report
    
    # Act
    result = await service.process_report(
        report_id=1,
        handler_id=2,
        action="reject"
    )
    
    # Assert
    assert result.status == ReportStatus.REJECTED


@pytest.mark.asyncio
async def test_process_already_processed_report(service, mock_repository):
    """Test processing already processed report fails"""
    # Arrange
    mock_report = Report(
        id=1,
        reporter_id=1,
        target_type=ReportTargetType.POST,
        target_id=100,
        reason="违规",
        status=ReportStatus.RESOLVED,  # Already processed
        created_at=datetime.now()
    )
    mock_repository.get_by_id.return_value = mock_report
    
    # Act & Assert
    with pytest.raises(ValidationError, match="已被处理"):
        await service.process_report(
            report_id=1,
            handler_id=2,
            action="approve"
        )


@pytest.mark.asyncio
async def test_get_target_report_count(service, mock_repository):
    """Test getting report count for a target"""
    # Arrange
    mock_repository.count_by_target.return_value = 5
    
    # Act
    count = await service.get_target_report_count(
        ReportTargetType.POST,
        100
    )
    
    # Assert
    assert count == 5
    mock_repository.count_by_target.assert_called_once_with(
        ReportTargetType.POST,
        100
    )
