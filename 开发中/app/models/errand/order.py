"""跑腿服务数据模型

包含ErrandOrder表模型
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
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ErrandStatus(str, Enum):
    """跑腿订单状态枚举"""
    
    PENDING = "pending"  # 待接单
    ACCEPTED = "accepted"  # 已接单
    DELIVERING = "delivering"  # 配送中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    DISPUTED = "disputed"  # 有纠纷


class ErrandOrder(Base):
    """跑腿订单表

    存储校园跑腿服务的订单信息
    """

    __tablename__ = "errand_orders"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="订单ID",
    )

    # 发布者和接单者
    publisher_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="发布者ID",
    )
    runner_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="接单者ID",
    )
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )

    # 订单内容
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="标题",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="详细描述",
    )
    pickup_location: Mapped[str] = mapped_column(
        String(200),
        nullable=True,
        comment="取件地点",
    )
    delivery_location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="送达地点",
    )
    
    # 费用和时间
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="跑腿费",
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="截止时间",
    )

    # 状态
    status: Mapped[ErrandStatus] = mapped_column(
        SQLEnum(ErrandStatus),
        nullable=False,
        default=ErrandStatus.PENDING,
        index=True,
        comment="订单状态",
    )
    
    # 安全与验证
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否公开可见",
    )
    verification_code: Mapped[Optional[str]] = mapped_column(
        String(6),
        nullable=True,
        comment="收货验证码",
    )
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="接单时间",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间",
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
        Index("idx_errand_school_status", "school_id", "status"),
        Index("idx_errand_publisher_created", "publisher_id", "created_at"),
    )
