"""课程相关的Pydantic模式

用于API请求和响应的数据验证
"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


# ==================== 学校相关模式 ====================


class SchoolCreate(BaseModel):
    """学校创建请求模式"""

    name: str = Field(..., min_length=1, max_length=200, description="学校名称")
    short_name: Optional[str] = Field(None, max_length=50, description="学校简称")
    province: Optional[str] = Field(None, max_length=50, description="省份")
    city: Optional[str] = Field(None, max_length=50, description="城市")
    logo: Optional[str] = Field(None, max_length=255, description="校徽URL")


class SchoolResponse(BaseModel):
    """学校响应模式"""

    id: int
    name: str
    short_name: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    logo: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SchoolListResponse(BaseModel):
    """学校列表响应模式"""

    schools: List[SchoolResponse]
    total: int
    page: int
    page_size: int


# ==================== 课程相关模式 ====================


class CourseCreate(BaseModel):
    """课程创建请求模式"""

    name: str = Field(..., min_length=1, max_length=200, description="课程名称")
    code: Optional[str] = Field(None, max_length=50, description="课程代码")
    department: Optional[str] = Field(None, max_length=100, description="院系")
    major: Optional[str] = Field(None, max_length=100, description="专业")
    teacher: Optional[str] = Field(None, max_length=100, description="授课教师")
    credits: Optional[Decimal] = Field(None, ge=0, le=10, description="学分")
    exam_type: Optional[str] = Field(None, description="考核方式")
    semester: Optional[str] = Field(None, max_length=20, description="学期")
    syllabus: Optional[str] = Field(None, description="教学大纲")

    @field_validator("exam_type")
    @classmethod
    def validate_exam_type(cls, v):
        if v is not None:
            valid_types = ["exam", "assessment", "practice"]
            if v not in valid_types:
                raise ValueError(
                    f"考核方式必须是以下之一: {', '.join(valid_types)}"
                )
        return v


class CourseUpdate(BaseModel):
    """课程更新请求模式"""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="课程名称")
    code: Optional[str] = Field(None, max_length=50, description="课程代码")
    department: Optional[str] = Field(None, max_length=100, description="院系")
    major: Optional[str] = Field(None, max_length=100, description="专业")
    teacher: Optional[str] = Field(None, max_length=100, description="授课教师")
    credits: Optional[Decimal] = Field(None, ge=0, le=10, description="学分")
    exam_type: Optional[str] = Field(None, description="考核方式")
    semester: Optional[str] = Field(None, max_length=20, description="学期")
    syllabus: Optional[str] = Field(None, description="教学大纲")

    @field_validator("exam_type")
    @classmethod
    def validate_exam_type(cls, v):
        if v is not None:
            valid_types = ["exam", "assessment", "practice"]
            if v not in valid_types:
                raise ValueError(
                    f"考核方式必须是以下之一: {', '.join(valid_types)}"
                )
        return v


class CourseResponse(BaseModel):
    """课程响应模式"""

    id: int
    school_id: int
    code: Optional[str] = None
    name: str
    department: Optional[str] = None
    major: Optional[str] = None
    teacher: Optional[str] = None
    credits: Optional[Decimal] = None
    exam_type: Optional[str] = None
    semester: Optional[str] = None
    syllabus: Optional[str] = None
    rating_count: int
    avg_rating: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    """课程详情响应模式（包含资料列表）"""

    materials: List["MaterialResponse"] = []


class CourseListResponse(BaseModel):
    """课程列表响应模式"""

    courses: List[CourseResponse]
    total: int
    page: int
    page_size: int


class DepartmentListResponse(BaseModel):
    """院系列表响应模式"""

    departments: List[str]


# ==================== 课程资料相关模式 ====================


class MaterialCreate(BaseModel):
    """课程资料创建请求模式"""

    name: str = Field(..., min_length=1, max_length=200, description="资料名称")
    type: str = Field(..., description="资料类型")
    file_url: Optional[str] = Field(None, max_length=500, description="文件URL")
    file_size: Optional[int] = Field(None, ge=0, description="文件大小（字节）")
    file_type: Optional[str] = Field(None, max_length=50, description="文件类型")
    description: Optional[str] = Field(None, description="资料描述")
    download_permission: str = Field(
        default="free", description="下载权限（free或points）"
    )
    points_cost: int = Field(default=0, ge=0, description="所需积分")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        valid_types = [
            "courseware",
            "outline",
            "exam",
            "homework",
            "report",
            "notes",
            "other",
        ]
        if v not in valid_types:
            raise ValueError(f"资料类型必须是以下之一: {', '.join(valid_types)}")
        return v

    @field_validator("download_permission")
    @classmethod
    def validate_download_permission(cls, v):
        valid_permissions = ["free", "points"]
        if v not in valid_permissions:
            raise ValueError(
                f"下载权限必须是以下之一: {', '.join(valid_permissions)}"
            )
        return v


class MaterialUpdate(BaseModel):
    """课程资料更新请求模式"""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="资料名称")
    description: Optional[str] = Field(None, description="资料描述")
    download_permission: Optional[str] = Field(None, description="下载权限")
    points_cost: Optional[int] = Field(None, ge=0, description="所需积分")
    is_featured: Optional[bool] = Field(None, description="是否精华资料")

    @field_validator("download_permission")
    @classmethod
    def validate_download_permission(cls, v):
        if v is not None:
            valid_permissions = ["free", "points"]
            if v not in valid_permissions:
                raise ValueError(
                    f"下载权限必须是以下之一: {', '.join(valid_permissions)}"
                )
        return v


class MaterialResponse(BaseModel):
    """课程资料响应模式"""

    id: int
    course_id: int
    uploader_id: int
    name: str
    type: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    download_permission: str
    points_cost: int
    download_count: int
    is_featured: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MaterialListResponse(BaseModel):
    """课程资料列表响应模式"""

    materials: List[MaterialResponse]
    total: int
    page: int
    page_size: int


class MaterialDownloadResponse(BaseModel):
    """课程资料下载响应模式"""

    download_url: str
    expires_in: int = Field(description="URL过期时间（秒）")


class MaterialPreviewResponse(BaseModel):
    """课程资料预览响应模式"""

    preview_url: str
    file_type: str = Field(description="文件类型")


# ==================== 课程交流区模式 ====================


class CoursePostCreate(BaseModel):
    """课程帖子创建请求模式"""

    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=1, description="内容")
    type: str = Field(default="discussion", description="类型(discussion/question/resource)")


class CoursePostResponse(BaseModel):
    """课程帖子响应模式"""

    id: int
    course_id: int
    user_id: int
    title: str
    content: str
    type: str
    view_count: int
    reply_count: int
    like_count: int
    is_pinned: bool
    is_essence: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoursePostListResponse(BaseModel):
    """课程帖子列表响应模式"""

    posts: List[CoursePostResponse]
    total: int
    page: int
    page_size: int


# ==================== 辅助函数 ====================


def school_to_response(school) -> SchoolResponse:
    """将School模型转换为SchoolResponse

    Args:
        school: School模型实例

    Returns:
        SchoolResponse
    """
    return SchoolResponse(
        id=school.id,
        name=school.name,
        short_name=school.short_name,
        province=school.province,
        city=school.city,
        logo=school.logo,
        status=school.status.value,
        created_at=school.created_at,
    )


def course_to_response(course) -> CourseResponse:
    """将Course模型转换为CourseResponse

    Args:
        course: Course模型实例

    Returns:
        CourseResponse
    """
    return CourseResponse(
        id=course.id,
        school_id=course.school_id,
        code=course.code,
        name=course.name,
        department=course.department,
        major=course.major,
        teacher=course.teacher,
        credits=course.credits,
        exam_type=course.exam_type.value if course.exam_type else None,
        semester=course.semester,
        syllabus=course.syllabus,
        rating_count=course.rating_count,
        avg_rating=course.avg_rating,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


def course_to_detail_response(course) -> CourseDetailResponse:
    """将Course模型转换为CourseDetailResponse（包含资料）

    Args:
        course: Course模型实例（需要加载materials关系）

    Returns:
        CourseDetailResponse
    """
    materials = []
    if hasattr(course, "materials") and course.materials:
        materials = [material_to_response(m) for m in course.materials]

    return CourseDetailResponse(
        id=course.id,
        school_id=course.school_id,
        code=course.code,
        name=course.name,
        department=course.department,
        major=course.major,
        teacher=course.teacher,
        credits=course.credits,
        exam_type=course.exam_type.value if course.exam_type else None,
        semester=course.semester,
        syllabus=course.syllabus,
        rating_count=course.rating_count,
        avg_rating=course.avg_rating,
        created_at=course.created_at,
        updated_at=course.updated_at,
        materials=materials,
    )


def material_to_response(material) -> MaterialResponse:
    """将CourseMaterial模型转换为MaterialResponse

    Args:
        material: CourseMaterial模型实例

    Returns:
        MaterialResponse
    """
    return MaterialResponse(
        id=material.id,
        course_id=material.course_id,
        uploader_id=material.uploader_id,
        name=material.name,
        type=material.type.value,
        file_url=material.file_url,
        file_size=material.file_size,
        file_type=material.file_type,
        description=material.description,
        download_permission=material.download_permission.value,
        points_cost=material.points_cost,
        download_count=material.download_count,
        is_featured=material.is_featured,
        status=material.status.value,
        created_at=material.created_at,
    )


def post_to_response(post) -> CoursePostResponse:
    """将CoursePost模型转换为CoursePostResponse

    Args:
        post: CoursePost模型实例

    Returns:
        CoursePostResponse
    """
    return CoursePostResponse(
        id=post.id,
        course_id=post.course_id,
        user_id=post.user_id,
        title=post.title,
        content=post.content,
        type=post.type,
        view_count=post.view_count,
        reply_count=post.reply_count,
        like_count=post.like_count,
        is_pinned=post.is_pinned,
        is_essence=post.is_essence,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )
