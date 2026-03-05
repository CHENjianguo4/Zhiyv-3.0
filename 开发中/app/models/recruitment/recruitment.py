"""搭子组队数据模型

包含Recruitment、Application、Group表模型
"""

from datetime import datetime
from typing import Optional
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    String,
    Text,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RecruitmentStatus(str, Enum):
    """招募状态枚举"""
    
    OPEN = "open"  # 开放中
    FULL = "full"  # 已满员
    CLOSED = "closed"  # 已关闭
    EXPIRED = "expired"  # 已过期


class ApplicationStatus(str, Enum):
    """申请状态枚举"""
    
    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消


class Recruitment(Base):
    """招募帖表

    存储搭子招募信息
    """

    __tablename__ = "recruitments"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="招募ID",
    )

    # 关联
    publisher_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="发布者ID",
    )
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )

    # 招募内容
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="标题",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="描述",
    )
    tags: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="标签(逗号分隔)",
    )
    
    # 限制条件
    target_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="目标人数",
    )
    current_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="当前人数",
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="截止时间",
    )
    
    # 状态
    status: Mapped[RecruitmentStatus] = mapped_column(
        SQLEnum(RecruitmentStatus),
        nullable=False,
        default=RecruitmentStatus.OPEN,
        index=True,
        comment="状态",
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    # 索引
    __table_args__ = (
        Index("idx_recruitment_school_status", "school_id", "status"),
        Index("idx_recruitment_publisher", "publisher_id"),
    )


class Application(Base):
    """入队申请表

    存储用户的入队申请
    """

    __tablename__ = "recruitment_applications"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="申请ID",
    )

    # 关联
    recruitment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("recruitments.id"),
        nullable=False,
        index=True,
        comment="招募ID",
    )
    applicant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="申请人ID",
    )

    # 申请内容
    reason: Mapped[str] = mapped_column(
        String(200),
        nullable=True,
        comment="申请理由",
    )
    contact: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="联系方式",
    )
    
    # 状态
    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.PENDING,
        comment="状态",
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    # 索引
    __table_args__ = (
        Index("idx_application_recruitment_user", "recruitment_id", "applicant_id", unique=True),
    )
