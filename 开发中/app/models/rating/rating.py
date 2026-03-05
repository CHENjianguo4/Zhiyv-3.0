"""评分体系数据模型

包含RatingSubject和Rating表模型
"""

from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    String,
    Text,
    Numeric,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SubjectType(str, Enum):
    """评分主体类型枚举"""
    
    COURSE = "course"  # 课程
    TEACHER = "teacher"  # 老师
    CANTEEN = "canteen"  # 食堂
    SHOP = "shop"  # 商铺
    SERVICE = "service"  # 服务部门
    OTHER = "other"  # 其他


class RatingSubject(Base):
    """评分主体表

    存储可被评分的对象（课程、食堂窗口、老师等）
    """

    __tablename__ = "rating_subjects"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主体ID",
    )

    # 关联
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )
    creator_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        comment="创建者ID",
    )

    # 基本信息
    type: Mapped[SubjectType] = mapped_column(
        SQLEnum(SubjectType),
        nullable=False,
        index=True,
        comment="类型",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="名称",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="描述",
    )
    cover_image: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="封面图",
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="位置信息",
    )
    
    # 统计数据
    rating_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 1),
        nullable=False,
        default=0.0,
        comment="综合评分",
    )
    rating_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="评分人数",
    )
    
    # 状态
    is_approved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否审核通过",
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
        Index("idx_subject_school_type", "school_id", "type"),
        Index("idx_subject_score", "rating_score"),
    )


class Rating(Base):
    """评分表

    存储用户的具体评分和评价
    """

    __tablename__ = "ratings"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="评分ID",
    )

    # 关联
    subject_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("rating_subjects.id"),
        nullable=False,
        index=True,
        comment="主体ID",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 评分内容
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="分数(1-5)",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="评价内容",
    )
    images: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="图片列表",
    )
    tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="评价标签",
    )
    
    # 互动数据
    like_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="点赞数",
    )
    
    # 状态
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否匿名",
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )

    # 索引
    __table_args__ = (
        Index("idx_rating_subject_created", "subject_id", "created_at"),
        Index("idx_rating_user_subject", "user_id", "subject_id", unique=True),
    )
