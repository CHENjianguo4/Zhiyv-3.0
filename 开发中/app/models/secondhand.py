"""二手商品相关数据模型

包含SecondhandItem、SecondhandOrder表模型
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ItemCategory(str, Enum):
    """商品分类枚举"""

    ELECTRONICS = "electronics"  # 电子产品
    TEXTBOOK = "textbook"  # 图书教材
    DAILY = "daily"  # 生活用品
    SPORTS = "sports"  # 运动器材
    OTHER = "other"  # 其他


class ItemCondition(str, Enum):
    """商品成色枚举"""

    BRAND_NEW = "brand_new"  # 全新
    LIKE_NEW = "like_new"  # 几乎全新
    LIGHTLY_USED = "lightly_used"  # 轻微使用
    WELL_USED = "well_used"  # 明显使用
    HEAVILY_USED = "heavily_used"  # 严重使用


class ItemStatus(str, Enum):
    """商品状态枚举"""

    DRAFT = "draft"  # 草稿
    ON_SALE = "on_sale"  # 在售
    SOLD = "sold"  # 已售出
    REMOVED = "removed"  # 已下架
    BANNED = "banned"  # 已封禁


class DeliveryMethod(str, Enum):
    """交易方式枚举"""

    FACE_TO_FACE = "face_to_face"  # 面交
    EXPRESS = "express"  # 快递
    BOTH = "both"  # 都可以


class OrderStatus(str, Enum):
    """订单状态枚举"""

    PENDING = "pending"  # 待确认
    CONFIRMED = "confirmed"  # 已确认
    DELIVERING = "delivering"  # 配送中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    DISPUTED = "disputed"  # 有纠纷


class PaymentStatus(str, Enum):
    """支付状态枚举"""

    UNPAID = "unpaid"  # 未支付
    PAID = "paid"  # 已支付
    REFUNDED = "refunded"  # 已退款


class SecondhandItem(Base):
    """二手商品表

    存储二手商品的详细信息
    """

    __tablename__ = "secondhand_items"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="商品ID",
    )

    # 卖家和学校信息
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="卖家ID",
    )
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )

    # 商品基本信息
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="商品标题",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="商品描述",
    )
    category: Mapped[ItemCategory] = mapped_column(
        SQLEnum(ItemCategory),
        nullable=False,
        index=True,
        comment="商品分类",
    )
    condition: Mapped[ItemCondition] = mapped_column(
        SQLEnum(ItemCondition),
        nullable=False,
        comment="成色",
    )

    # 价格信息
    original_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="原价",
    )
    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="售价",
    )

    # 媒体文件
    images: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="图片URLs（JSON数组）",
    )
    videos: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="视频URLs（JSON数组）",
    )

    # 交易信息
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="交易地点",
    )
    is_negotiable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否可议价",
    )
    delivery_method: Mapped[DeliveryMethod] = mapped_column(
        SQLEnum(DeliveryMethod),
        nullable=False,
        comment="交易方式",
    )

    # 状态和统计
    status: Mapped[ItemStatus] = mapped_column(
        SQLEnum(ItemStatus),
        nullable=False,
        default=ItemStatus.DRAFT,
        index=True,
        comment="状态",
    )
    view_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="浏览次数",
    )
    favorite_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="收藏次数",
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
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="删除时间（软删除）",
    )

    # 索引
    __table_args__ = (
        Index("idx_school_id", "school_id"),
        Index("idx_seller_id", "seller_id"),
        Index("idx_category", "category"),
        Index("idx_status", "status"),
        Index("idx_school_category_status", "school_id", "category", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<SecondhandItem(id={self.id}, "
            f"title={self.title}, "
            f"seller_id={self.seller_id}, "
            f"price={self.selling_price}, "
            f"status={self.status})>"
        )


class SecondhandOrder(Base):
    """二手交易订单表

    存储二手商品的交易订单信息
    """

    __tablename__ = "secondhand_orders"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="订单ID",
    )

    # 商品和用户信息
    item_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="商品ID",
    )
    buyer_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="买家ID",
    )
    seller_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="卖家ID",
    )
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )

    # 交易信息
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="成交价格",
    )
    delivery_method: Mapped[DeliveryMethod] = mapped_column(
        SQLEnum(DeliveryMethod),
        nullable=False,
        comment="交易方式",
    )
    delivery_address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="收货地址",
    )

    # 订单状态
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
        comment="订单状态",
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.UNPAID,
        comment="支付状态",
    )

    # 担保金额
    escrow_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="担保金额",
    )

    # 备注
    buyer_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="买家备注",
    )
    seller_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="卖家备注",
    )

    # 完成时间
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间",
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
        Index("idx_item_id", "item_id"),
        Index("idx_buyer_id", "buyer_id"),
        Index("idx_seller_id", "seller_id"),
        Index("idx_school_id", "school_id"),
        Index("idx_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<SecondhandOrder(id={self.id}, "
            f"item_id={self.item_id}, "
            f"buyer_id={self.buyer_id}, "
            f"seller_id={self.seller_id}, "
            f"price={self.price}, "
            f"status={self.status})>"
        )


class ItemFavorite(Base):
    """商品收藏表

    存储用户收藏的二手商品
    """

    __tablename__ = "item_favorites"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="收藏ID",
    )

    # 用户和商品信息
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="用户ID",
    )
    item_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="商品ID",
    )
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )

    # 索引和约束
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_item_id", "item_id"),
        Index("idx_school_id", "school_id"),
        Index("uk_user_item", "user_id", "item_id", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<ItemFavorite(id={self.id}, "
            f"user_id={self.user_id}, "
            f"item_id={self.item_id})>"
        )


class PriceAlert(Base):
    """降价提醒表

    存储用户设置的商品降价提醒
    """

    __tablename__ = "price_alerts"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="提醒ID",
    )

    # 用户和商品信息
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="用户ID",
    )
    item_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="商品ID",
    )
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )

    # 提醒设置
    target_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="目标价格",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否激活",
    )
    notified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="通知时间",
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

    # 索引和约束
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_item_id", "item_id"),
        Index("idx_school_id", "school_id"),
        Index("idx_is_active", "is_active"),
        Index("uk_user_item_alert", "user_id", "item_id", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<PriceAlert(id={self.id}, "
            f"user_id={self.user_id}, "
            f"item_id={self.item_id}, "
            f"target_price={self.target_price}, "
            f"is_active={self.is_active})>"
        )
