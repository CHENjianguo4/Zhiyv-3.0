"""通知数据模型

包含Notification表模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Notification(Base):
    """通知表

    存储系统通知、业务通知等
    """

    __tablename__ = "notifications"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="通知ID",
    )

    # 接收者
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="接收用户ID",
    )

    # 通知内容
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="通知类型(system/like/comment/order/etc)",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="标题",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="内容",
    )
    data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="扩展数据(跳转链接等)",
    )

    # 状态
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否已读",
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
        Index("idx_notification_user_read", "user_id", "is_read"),
        Index("idx_notification_created", "created_at"),
    )
