"""IM相关数据模型

包含Conversation、Message表模型
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Conversation(Base):
    """会话表

    存储一对一私信或群组聊天的会话信息
    """

    __tablename__ = "conversations"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="会话ID",
    )

    # 会话类型
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="private",
        comment="类型(private/group)",
    )

    # 关联信息
    name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="会话名称(群组)",
    )
    avatar: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="会话头像(群组)",
    )
    owner_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        comment="群主ID",
    )

    # 状态
    last_message_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="最后一条消息ID",
    )
    last_message_content: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="最后一条消息内容摘要",
    )
    last_message_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后一条消息时间",
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
        Index("idx_conversation_updated", "updated_at"),
    )


class ConversationMember(Base):
    """会话成员表

    存储会话参与者信息
    """

    __tablename__ = "conversation_members"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="成员ID",
    )

    # 关联
    conversation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("conversations.id"),
        nullable=False,
        index=True,
        comment="会话ID",
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 状态
    unread_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="未读消息数",
    )
    is_muted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否免打扰",
    )
    is_top: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否置顶",
    )

    # 时间戳
    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="加入时间",
    )
    last_read_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="最后阅读时间",
    )

    # 索引
    __table_args__ = (
        Index("idx_member_conversation_user", "conversation_id", "user_id", unique=True),
    )
