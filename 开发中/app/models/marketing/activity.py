"""营销工具数据模型

包含Activity、Coupon表模型
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
    JSON,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ActivityType(str, Enum):
    """活动类型枚举"""
    
    SIGN_IN = "sign_in"  # 签到
    LUCKY_DRAW = "draw"  # 抽奖
    TASK = "task"  # 任务
    INVITE = "invite"  # 邀请


class Activity(Base):
    """活动表

    存储运营活动信息
    """

    __tablename__ = "marketing_activities"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="活动ID",
    )

    # 基本信息
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="标题",
    )
    type: Mapped[ActivityType] = mapped_column(
        SQLEnum(ActivityType),
        nullable=False,
        index=True,
        comment="类型",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="描述",
    )
    rules: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment="活动规则",
    )
    rewards: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment="奖励配置",
    )
    
    # 时间范围
    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="开始时间",
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="结束时间",
    )
    
    # 状态
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用",
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


class Coupon(Base):
    """优惠券表

    存储优惠券信息
    """

    __tablename__ = "marketing_coupons"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="优惠券ID",
    )

    # 关联
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="所属用户ID",
    )
    activity_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("marketing_activities.id"),
        nullable=True,
        comment="来源活动ID",
    )

    # 券信息
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="名称",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="面额",
    )
    min_spend: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0,
        comment="最低消费",
    )
    
    # 状态
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否已使用",
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="使用时间",
    )
    expire_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="过期时间",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="领取时间",
    )
