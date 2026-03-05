"""
Circle Model

Defines the database model for circles (community boards).
"""
from sqlalchemy import Column, BigInteger, String, Enum, Text, JSON, Integer, TIMESTAMP, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base
import enum

# Import School from course module to avoid duplicate definition
from app.models.course import School


class CircleType(str, enum.Enum):
    """Circle type"""
    OFFICIAL = "official"  # Official circles
    CUSTOM = "custom"      # User-created circles


class CircleStatus(str, enum.Enum):
    """Circle status"""
    ACTIVE = "active"
    ARCHIVED = "archived"


class Circle(Base):
    """Circle model for community boards"""
    __tablename__ = "circles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    school_id = Column(BigInteger, ForeignKey("schools.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(255))
    type = Column(Enum(CircleType), nullable=False, default=CircleType.CUSTOM)
    creator_id = Column(BigInteger, ForeignKey("users.id"))
    admin_ids = Column(JSON)  # List of admin user IDs
    member_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    status = Column(Enum(CircleStatus), nullable=False, default=CircleStatus.ACTIVE)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_school_id', 'school_id'),
        Index('idx_type', 'type'),
        Index('idx_status', 'status'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "school_id": self.school_id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "type": self.type.value if self.type else None,
            "creator_id": self.creator_id,
            "admin_ids": self.admin_ids or [],
            "member_count": self.member_count,
            "post_count": self.post_count,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
