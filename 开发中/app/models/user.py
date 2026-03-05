"""用户相关数据模型

包含User、UserProfile、CreditLog、PointLog表模型
"""

from datetime import datetime
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
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, Enum):
    """用户角色枚举"""

    STUDENT = "student"
    TEACHER = "teacher"
    MERCHANT = "merchant"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """用户状态枚举"""

    ACTIVE = "active"
    BANNED = "banned"
    DELETED = "deleted"


class User(Base):
    """用户表

    存储用户基本信息、认证状态、信用分、积分等核心数据
    """

    __tablename__ = "users"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="用户ID",
    )

    # 微信相关
    wechat_openid: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="微信OpenID",
    )
    wechat_unionid: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="微信UnionID",
    )

    # 基本信息
    nickname: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="昵称",
    )
    avatar: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="头像URL",
    )

    # 学校和身份信息
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
        comment="学校ID",
    )
    student_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="学号",
    )
    real_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="真实姓名",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="邮箱",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="手机号",
    )

    # 角色和状态
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        nullable=False,
        default=UserRole.STUDENT,
        comment="用户角色",
    )
    verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否已认证",
    )

    # 信用分和积分
    credit_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=80,
        index=True,
        comment="信用分（默认80）",
    )
    points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="积分（默认0）",
    )

    # 账号状态
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus),
        nullable=False,
        default=UserStatus.ACTIVE,
        comment="账号状态",
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

    # 关系
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    credit_logs: Mapped[list["CreditLog"]] = relationship(
        "CreditLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    point_logs: Mapped[list["PointLog"]] = relationship(
        "PointLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index("idx_school_id", "school_id"),
        Index("idx_student_id", "student_id"),
        Index("idx_credit_score", "credit_score"),
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, "
            f"nickname={self.nickname}, "
            f"school_id={self.school_id}, "
            f"verified={self.verified}, "
            f"credit_score={self.credit_score})>"
        )


class UserProfile(Base):
    """用户档案表

    存储用户的详细档案信息，包括年级、专业、兴趣标签等
    """

    __tablename__ = "user_profiles"

    # 主键（同时也是外键）
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID",
    )

    # 学业信息
    grade: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="年级",
    )
    major: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="专业",
    )
    campus: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="校区",
    )

    # 兴趣标签（JSON数组）
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="兴趣标签（JSON数组）",
    )

    # 个人简介
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="个人简介",
    )

    # 隐私设置（JSON对象）
    privacy_settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="隐私设置（JSON对象）",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
    )

    def __repr__(self) -> str:
        return (
            f"<UserProfile(user_id={self.user_id}, "
            f"grade={self.grade}, "
            f"major={self.major}, "
            f"campus={self.campus})>"
        )


class CreditLog(Base):
    """信用分记录表

    记录用户信用分的所有变更历史
    """

    __tablename__ = "credit_logs"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="记录ID",
    )

    # 用户ID
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 变更金额
    change_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="变更金额（正数为增加，负数为减少）",
    )

    # 变更原因
    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="变更原因",
    )

    # 关联对象
    related_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="关联对象类型（post/order/rating/violation）",
    )
    related_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="关联对象ID",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="创建时间",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="credit_logs",
    )

    # 索引
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<CreditLog(id={self.id}, "
            f"user_id={self.user_id}, "
            f"change_amount={self.change_amount}, "
            f"reason={self.reason})>"
        )


class PointLog(Base):
    """积分记录表

    记录用户积分的所有变更历史
    """

    __tablename__ = "point_logs"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="记录ID",
    )

    # 用户ID
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # 变更金额
    change_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="变更金额（正数为增加，负数为减少）",
    )

    # 动作类型
    action_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="动作类型（post/order/rating/material等）",
    )

    # 描述
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="描述",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )

    # 关系
    user: Mapped["User"] = relationship(
        "User",
        back_populates="point_logs",
    )

    # 索引
    __table_args__ = (Index("idx_user_id", "user_id"),)

    def __repr__(self) -> str:
        return (
            f"<PointLog(id={self.id}, "
            f"user_id={self.user_id}, "
            f"change_amount={self.change_amount}, "
            f"action_type={self.action_type})>"
        )
