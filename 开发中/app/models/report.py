"""
Report Model

Defines the database model for user reports.
"""
from sqlalchemy import Column, BigInteger, String, Enum, Text, JSON, TIMESTAMP, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ReportTargetType(str, enum.Enum):
    """Type of reported target"""
    POST = "post"
    COMMENT = "comment"
    USER = "user"
    ITEM = "item"  # secondhand item
    ORDER = "order"


class ReportStatus(str, enum.Enum):
    """Report processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Report(Base):
    """Report model for content and user reports"""
    __tablename__ = "reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reporter_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    target_type = Column(Enum(ReportTargetType), nullable=False)
    target_id = Column(BigInteger, nullable=False)
    reason = Column(String(255))
    description = Column(Text)
    evidence = Column(JSON)  # Screenshots, links, etc.
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.PENDING)
    handler_id = Column(BigInteger, ForeignKey("users.id"))
    handle_result = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_target', 'target_type', 'target_id'),
        Index('idx_reporter_id', 'reporter_id'),
        Index('idx_created_at', 'created_at'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "target_type": self.target_type.value if self.target_type else None,
            "target_id": self.target_id,
            "reason": self.reason,
            "description": self.description,
            "evidence": self.evidence,
            "status": self.status.value if self.status else None,
            "handler_id": self.handler_id,
            "handle_result": self.handle_result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
