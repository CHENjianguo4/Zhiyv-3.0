"""课程相关数据模型

包含School、Course、CourseMaterial表模型
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import (
    DECIMAL,
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


class SchoolStatus(str, Enum):
    """学校状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"


class ExamType(str, Enum):
    """考核方式枚举"""

    EXAM = "exam"  # 考试
    ASSESSMENT = "assessment"  # 考查
    PRACTICE = "practice"  # 实践


class MaterialType(str, Enum):
    """资料类型枚举"""

    COURSEWARE = "courseware"  # 课件
    OUTLINE = "outline"  # 复习提纲
    EXAM = "exam"  # 历年真题
    HOMEWORK = "homework"  # 作业答案
    REPORT = "report"  # 实验报告
    NOTES = "notes"  # 手写笔记
    OTHER = "other"  # 其他


class DownloadPermission(str, Enum):
    """下载权限枚举"""

    FREE = "free"  # 免费下载
    POINTS = "points"  # 积分兑换


class MaterialStatus(str, Enum):
    """资料状态枚举"""

    PENDING = "pending"  # 待审核
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝


class School(Base):
    """学校表

    存储学校基本信息
    """

    __tablename__ = "schools"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="学校ID",
    )

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="学校名称",
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="学校简称",
    )

    # 地理位置
    province: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="省份",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="城市",
    )

    # 其他信息
    logo: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="校徽URL",
    )

    # 状态
    status: Mapped[SchoolStatus] = mapped_column(
        SQLEnum(SchoolStatus),
        nullable=False,
        default=SchoolStatus.ACTIVE,
        comment="学校状态",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )

    # 关系
    courses: Mapped[list["Course"]] = relationship(
        "Course",
        back_populates="school",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<School(id={self.id}, "
            f"name={self.name}, "
            f"status={self.status})>"
        )


class Course(Base):
    """课程表

    存储课程基本信息和评分数据
    """

    __tablename__ = "courses"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="课程ID",
    )

    # 学校关联
    school_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("schools.id"),
        nullable=False,
        index=True,
        comment="学校ID",
    )

    # 课程基本信息
    code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="课程代码",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="课程名称",
    )

    # 院系专业信息
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="院系",
    )
    major: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="专业",
    )

    # 教师信息
    teacher: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="授课教师",
    )

    # 学分和考核
    credits: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 1),
        nullable=True,
        comment="学分",
    )
    exam_type: Mapped[Optional[ExamType]] = mapped_column(
        SQLEnum(ExamType),
        nullable=True,
        comment="考核方式",
    )

    # 学期信息
    semester: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="学期（春季、秋季、夏季）",
    )

    # 课程大纲
    syllabus: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="教学大纲",
    )

    # 评分统计
    rating_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="评分次数",
    )
    avg_rating: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2),
        nullable=True,
        comment="平均评分",
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
    school: Mapped["School"] = relationship(
        "School",
        back_populates="courses",
    )
    materials: Mapped[list["CourseMaterial"]] = relationship(
        "CourseMaterial",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    # 索引
    __table_args__ = (
        Index("idx_school_id", "school_id"),
        Index("idx_department", "department"),
        Index("idx_teacher", "teacher"),
    )

    def __repr__(self) -> str:
        return (
            f"<Course(id={self.id}, "
            f"name={self.name}, "
            f"code={self.code}, "
            f"teacher={self.teacher})>"
        )


class CourseMaterial(Base):
    """课程资料表

    存储课程相关的学习资料
    """

    __tablename__ = "course_materials"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="资料ID",
    )

    # 课程关联
    course_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
        comment="课程ID",
    )

    # 上传者关联
    uploader_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="上传者ID",
    )

    # 资料基本信息
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="资料名称",
    )
    type: Mapped[MaterialType] = mapped_column(
        SQLEnum(MaterialType),
        nullable=False,
        index=True,
        comment="资料类型",
    )

    # 文件信息
    file_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="文件URL",
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="文件大小（字节）",
    )
    file_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="文件类型（扩展名）",
    )

    # 资料描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="资料描述",
    )

    # 下载权限
    download_permission: Mapped[DownloadPermission] = mapped_column(
        SQLEnum(DownloadPermission),
        nullable=False,
        default=DownloadPermission.FREE,
        comment="下载权限",
    )
    points_cost: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="所需积分（如果需要积分）",
    )

    # 统计数据
    download_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="下载次数",
    )

    # 精华标记
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否精华资料",
    )

    # 审核状态
    status: Mapped[MaterialStatus] = mapped_column(
        SQLEnum(MaterialStatus),
        nullable=False,
        default=MaterialStatus.PENDING,
        index=True,
        comment="审核状态",
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )

    # 关系
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="materials",
    )

    # 索引
    __table_args__ = (
        Index("idx_material_course_type", "course_id", "type"),
        Index("idx_material_uploader", "uploader_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<CourseMaterial(id={self.id}, "
            f"name={self.name}, "
            f"type={self.type}, "
            f"status={self.status})>"
        )


class CoursePost(Base):
    """课程交流区帖子表

    存储课程相关的讨论帖子
    """

    __tablename__ = "course_posts"

    # 主键
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="帖子ID",
    )

    # 课程关联
    course_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
        comment="课程ID",
    )

    # 发布者关联
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        comment="发布者ID",
    )

    # 帖子内容
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
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="discussion",
        comment="类型(discussion/question/resource)",
    )

    # 统计数据
    view_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="浏览次数",
    )
    reply_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="回复次数",
    )
    like_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="点赞次数",
    )

    # 状态
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否置顶",
    )
    is_essence: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否精华",
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
        Index("idx_post_course_created", "course_id", "created_at"),
    )
