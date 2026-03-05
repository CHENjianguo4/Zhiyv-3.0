"""课程服务

提供课程库管理的业务逻辑
"""

from typing import List, Optional, Tuple
from decimal import Decimal

from app.repositories.course import (
    SchoolRepository,
    CourseRepository,
    CourseMaterialRepository,
    CoursePostRepository,
)
from app.models.course import (
    School,
    Course,
    CourseMaterial,
    CoursePost,
    ExamType,
    MaterialType,
    MaterialStatus,
    DownloadPermission,
)
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
)
from app.core.logging import get_logger
from app.services.content_audit import ContentAuditEngine

logger = get_logger(__name__)


class SchoolService:
    """学校服务类

    提供学校管理的业务逻辑
    """

    def __init__(self, school_repository: SchoolRepository):
        """初始化服务

        Args:
            school_repository: 学校仓储
        """
        self.school_repo = school_repository

    async def create_school(
        self,
        name: str,
        short_name: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        logo: Optional[str] = None,
    ) -> School:
        """创建学校

        Args:
            name: 学校名称
            short_name: 学校简称
            province: 省份
            city: 城市
            logo: 校徽URL

        Returns:
            School: 创建的学校对象

        Raises:
            ValidationError: 验证失败
        """
        # 验证必填字段
        if not name or len(name.strip()) == 0:
            raise ValidationError("学校名称不能为空")

        if len(name) > 200:
            raise ValidationError("学校名称不能超过200个字符")

        # 检查学校名称是否已存在
        existing_school = await self.school_repo.get_school_by_name(name)
        if existing_school:
            raise ValidationError(f"学校名称已存在: {name}")

        # 创建学校
        school = School(
            name=name,
            short_name=short_name,
            province=province,
            city=city,
            logo=logo,
        )

        created_school = await self.school_repo.create_school(school)

        logger.info(
            "学校创建成功",
            school_id=created_school.id,
            name=name,
        )

        return created_school

    async def get_school(self, school_id: int) -> School:
        """获取学校信息

        Args:
            school_id: 学校ID

        Returns:
            School: 学校对象

        Raises:
            ResourceNotFoundError: 学校不存在
        """
        school = await self.school_repo.get_school_by_id(school_id)
        if not school:
            raise ResourceNotFoundError(f"学校不存在: {school_id}")

        return school

    async def list_schools(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[School], int]:
        """获取学校列表

        Args:
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            Tuple[List[School], int]: 学校列表和总数
        """
        offset = (page - 1) * page_size

        schools = await self.school_repo.list_active_schools(
            offset=offset,
            limit=page_size,
        )

        total = await self.school_repo.count_schools()

        logger.info(
            "获取学校列表",
            page=page,
            page_size=page_size,
            count=len(schools),
            total=total,
        )

        return schools, total


class CourseService:
    """课程服务类

    提供课程管理的业务逻辑
    """

    def __init__(
        self,
        course_repository: CourseRepository,
        school_repository: SchoolRepository,
    ):
        """初始化服务

        Args:
            course_repository: 课程仓储
            school_repository: 学校仓储
        """
        self.course_repo = course_repository
        self.school_repo = school_repository

    async def create_course(
        self,
        school_id: int,
        name: str,
        code: Optional[str] = None,
        department: Optional[str] = None,
        major: Optional[str] = None,
        teacher: Optional[str] = None,
        credits: Optional[Decimal] = None,
        exam_type: Optional[str] = None,
        semester: Optional[str] = None,
        syllabus: Optional[str] = None,
    ) -> Course:
        """创建课程

        Args:
            school_id: 学校ID
            name: 课程名称
            code: 课程代码
            department: 院系
            major: 专业
            teacher: 授课教师
            credits: 学分
            exam_type: 考核方式
            semester: 学期
            syllabus: 教学大纲

        Returns:
            Course: 创建的课程对象

        Raises:
            ValidationError: 验证失败
            ResourceNotFoundError: 学校不存在
        """
        # 验证学校是否存在
        school = await self.school_repo.get_school_by_id(school_id)
        if not school:
            raise ResourceNotFoundError(f"学校不存在: {school_id}")

        # 验证必填字段
        if not name or len(name.strip()) == 0:
            raise ValidationError("课程名称不能为空")

        if len(name) > 200:
            raise ValidationError("课程名称不能超过200个字符")

        # 验证课程代码唯一性（如果提供）
        if code:
            existing_course = await self.course_repo.get_course_by_code(
                school_id=school_id,
                code=code,
            )
            if existing_course:
                raise ValidationError(f"课程代码已存在: {code}")

        # 验证考核方式
        exam_type_enum = None
        if exam_type:
            try:
                exam_type_enum = ExamType(exam_type)
            except ValueError:
                raise ValidationError(f"无效的考核方式: {exam_type}")

        # 创建课程
        course = Course(
            school_id=school_id,
            name=name,
            code=code,
            department=department,
            major=major,
            teacher=teacher,
            credits=credits,
            exam_type=exam_type_enum,
            semester=semester,
            syllabus=syllabus,
        )

        created_course = await self.course_repo.create_course(course)

        logger.info(
            "课程创建成功",
            course_id=created_course.id,
            school_id=school_id,
            name=name,
            code=code,
        )

        return created_course

    async def get_course(
        self,
        course_id: int,
        load_materials: bool = False,
    ) -> Course:
        """获取课程详情

        Args:
            course_id: 课程ID
            load_materials: 是否加载课程资料

        Returns:
            Course: 课程对象

        Raises:
            ResourceNotFoundError: 课程不存在
        """
        course = await self.course_repo.get_course_by_id(
            course_id=course_id,
            load_materials=load_materials,
        )
        if not course:
            raise ResourceNotFoundError(f"课程不存在: {course_id}")

        return course

    async def update_course(
        self,
        course_id: int,
        name: Optional[str] = None,
        code: Optional[str] = None,
        department: Optional[str] = None,
        major: Optional[str] = None,
        teacher: Optional[str] = None,
        credits: Optional[Decimal] = None,
        exam_type: Optional[str] = None,
        semester: Optional[str] = None,
        syllabus: Optional[str] = None,
    ) -> Course:
        """更新课程信息

        Args:
            course_id: 课程ID
            name: 课程名称
            code: 课程代码
            department: 院系
            major: 专业
            teacher: 授课教师
            credits: 学分
            exam_type: 考核方式
            semester: 学期
            syllabus: 教学大纲

        Returns:
            Course: 更新后的课程对象

        Raises:
            ValidationError: 验证失败
            ResourceNotFoundError: 课程不存在
        """
        # 获取课程
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise ResourceNotFoundError(f"课程不存在: {course_id}")

        # 更新字段
        if name is not None:
            if len(name) > 200:
                raise ValidationError("课程名称不能超过200个字符")
            course.name = name

        if code is not None:
            # 检查课程代码唯一性
            existing_course = await self.course_repo.get_course_by_code(
                school_id=course.school_id,
                code=code,
            )
            if existing_course and existing_course.id != course_id:
                raise ValidationError(f"课程代码已存在: {code}")
            course.code = code

        if department is not None:
            course.department = department

        if major is not None:
            course.major = major

        if teacher is not None:
            course.teacher = teacher

        if credits is not None:
            course.credits = credits

        if exam_type is not None:
            try:
                course.exam_type = ExamType(exam_type)
            except ValueError:
                raise ValidationError(f"无效的考核方式: {exam_type}")

        if semester is not None:
            course.semester = semester

        if syllabus is not None:
            course.syllabus = syllabus

        # 更新课程
        updated_course = await self.course_repo.update_course(course)

        logger.info(
            "课程更新成功",
            course_id=course_id,
        )

        return updated_course

    async def delete_course(self, course_id: int) -> bool:
        """删除课程

        Args:
            course_id: 课程ID

        Returns:
            bool: 是否删除成功

        Raises:
            ResourceNotFoundError: 课程不存在
        """
        # 获取课程
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise ResourceNotFoundError(f"课程不存在: {course_id}")

        # 删除课程
        await self.course_repo.delete_course(course)

        logger.info(
            "课程删除成功",
            course_id=course_id,
        )

        return True

    async def list_courses(
        self,
        school_id: int,
        department: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Course], int]:
        """获取课程列表

        Args:
            school_id: 学校ID
            department: 院系（可选）
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            Tuple[List[Course], int]: 课程列表和总数
        """
        offset = (page - 1) * page_size

        if department:
            courses = await self.course_repo.list_courses_by_department(
                school_id=school_id,
                department=department,
                offset=offset,
                limit=page_size,
            )
        else:
            courses = await self.course_repo.list_courses_by_school(
                school_id=school_id,
                offset=offset,
                limit=page_size,
            )

        total = await self.course_repo.count_courses(
            school_id=school_id,
            department=department,
        )

        logger.info(
            "获取课程列表",
            school_id=school_id,
            department=department,
            page=page,
            page_size=page_size,
            count=len(courses),
            total=total,
        )

        return courses, total

    async def search_courses(
        self,
        school_id: int,
        keyword: Optional[str] = None,
        department: Optional[str] = None,
        teacher: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Course], int]:
        """搜索课程

        Args:
            school_id: 学校ID
            keyword: 关键词（搜索课程名称和代码）
            department: 院系
            teacher: 教师
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            Tuple[List[Course], int]: 课程列表和总数
        """
        offset = (page - 1) * page_size

        courses = await self.course_repo.search_courses(
            school_id=school_id,
            keyword=keyword,
            department=department,
            teacher=teacher,
            offset=offset,
            limit=page_size,
        )

        # TODO: 添加总数查询
        total = len(courses)

        logger.info(
            "搜索课程",
            school_id=school_id,
            keyword=keyword,
            department=department,
            teacher=teacher,
            page=page,
            page_size=page_size,
            count=len(courses),
        )

        return courses, total

    async def list_departments(
        self,
        school_id: int,
    ) -> List[str]:
        """获取学校的院系列表

        Args:
            school_id: 学校ID

        Returns:
            List[str]: 院系列表
        """
        # 获取该学校的所有课程
        courses = await self.course_repo.list_courses_by_school(
            school_id=school_id,
            offset=0,
            limit=10000,  # 获取所有课程
        )

        # 提取唯一的院系
        departments = set()
        for course in courses:
            if course.department:
                departments.add(course.department)

        department_list = sorted(list(departments))

        logger.info(
            "获取院系列表",
            school_id=school_id,
            count=len(department_list),
        )

        return department_list


class CourseMaterialService:
    """课程资料服务类

    提供课程资料管理的业务逻辑
    """

    def __init__(
        self,
        material_repository: CourseMaterialRepository,
        course_repository: CourseRepository,
        audit_engine: Optional[ContentAuditEngine] = None,
    ):
        """初始化服务

        Args:
            material_repository: 课程资料仓储
            course_repository: 课程仓储
            audit_engine: 内容审核引擎（可选）
        """
        self.material_repo = material_repository
        self.course_repo = course_repository
        self.audit_engine = audit_engine

    async def create_material(
        self,
        course_id: int,
        uploader_id: int,
        name: str,
        material_type: str,
        file_url: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        description: Optional[str] = None,
        download_permission: str = "free",
        points_cost: int = 0,
    ) -> CourseMaterial:
        """创建课程资料

        Args:
            course_id: 课程ID
            uploader_id: 上传者ID
            name: 资料名称
            material_type: 资料类型
            file_url: 文件URL
            file_size: 文件大小（字节）
            file_type: 文件类型（扩展名）
            description: 资料描述
            download_permission: 下载权限（free或points）
            points_cost: 所需积分

        Returns:
            CourseMaterial: 创建的课程资料对象

        Raises:
            ValidationError: 验证失败
            ResourceNotFoundError: 课程不存在
        """
        # 验证课程是否存在
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise ResourceNotFoundError(f"课程不存在: {course_id}")

        # 验证必填字段
        if not name or len(name.strip()) == 0:
            raise ValidationError("资料名称不能为空")

        if len(name) > 200:
            raise ValidationError("资料名称不能超过200个字符")

        # 验证资料类型
        try:
            material_type_enum = MaterialType(material_type)
        except ValueError:
            raise ValidationError(f"无效的资料类型: {material_type}")

        # 验证下载权限
        try:
            download_permission_enum = DownloadPermission(download_permission)
        except ValueError:
            raise ValidationError(f"无效的下载权限: {download_permission}")

        # 验证积分设置
        if download_permission_enum == DownloadPermission.POINTS and points_cost <= 0:
            raise ValidationError("积分兑换资料必须设置积分成本")

        # 验证文件类型（如果提供）
        if file_type:
            allowed_types = [
                "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
                "jpg", "jpeg", "png", "gif",
                "mp4", "avi", "mov",
                "zip", "rar", "7z"
            ]
            if file_type.lower() not in allowed_types:
                raise ValidationError(
                    f"不支持的文件类型: {file_type}。"
                    f"支持的类型: {', '.join(allowed_types)}"
                )

        # 内容审核（审核标题和描述）
        audit_passed = True
        audit_reason = None

        if self.audit_engine:
            audit_content = f"{name} {description or ''}"
            audit_result = await self.audit_engine.audit_text(
                content=audit_content,
                strict_mode=False,
            )

            if not audit_result.passed:
                audit_passed = False
                audit_reason = audit_result.reason

                logger.warning(
                    "资料内容审核未通过",
                    course_id=course_id,
                    uploader_id=uploader_id,
                    name=name,
                    reason=audit_reason,
                    found_words=audit_result.found_words,
                )

        # 创建资料
        material = CourseMaterial(
            course_id=course_id,
            uploader_id=uploader_id,
            name=name,
            type=material_type_enum,
            file_url=file_url,
            file_size=file_size,
            file_type=file_type,
            description=description,
            download_permission=download_permission_enum,
            points_cost=points_cost,
            status=MaterialStatus.APPROVED if audit_passed else MaterialStatus.PENDING,
        )

        created_material = await self.material_repo.create_material(material)

        logger.info(
            "课程资料创建成功",
            material_id=created_material.id,
            course_id=course_id,
            uploader_id=uploader_id,
            name=name,
            status=created_material.status.value,
        )

        return created_material

    async def get_material(self, material_id: int) -> CourseMaterial:
        """获取课程资料详情

        Args:
            material_id: 资料ID

        Returns:
            CourseMaterial: 课程资料对象

        Raises:
            ResourceNotFoundError: 资料不存在
        """
        material = await self.material_repo.get_material_by_id(material_id)
        if not material:
            raise ResourceNotFoundError(f"课程资料不存在: {material_id}")

        return material

    async def update_material(
        self,
        material_id: int,
        uploader_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        download_permission: Optional[str] = None,
        points_cost: Optional[int] = None,
        is_featured: Optional[bool] = None,
    ) -> CourseMaterial:
        """更新课程资料

        Args:
            material_id: 资料ID
            uploader_id: 上传者ID（用于权限验证）
            name: 资料名称
            description: 资料描述
            download_permission: 下载权限
            points_cost: 所需积分
            is_featured: 是否精华资料

        Returns:
            CourseMaterial: 更新后的课程资料对象

        Raises:
            ValidationError: 验证失败
            ResourceNotFoundError: 资料不存在
            PermissionDeniedError: 权限不足
        """
        # 获取资料
        material = await self.material_repo.get_material_by_id(material_id)
        if not material:
            raise ResourceNotFoundError(f"课程资料不存在: {material_id}")

        # 验证权限（只有上传者可以修改）
        if material.uploader_id != uploader_id:
            raise PermissionDeniedError("只有上传者可以修改资料")

        # 更新字段
        if name is not None:
            if len(name) > 200:
                raise ValidationError("资料名称不能超过200个字符")
            material.name = name

        if description is not None:
            material.description = description

        if download_permission is not None:
            try:
                material.download_permission = DownloadPermission(download_permission)
            except ValueError:
                raise ValidationError(f"无效的下载权限: {download_permission}")

        if points_cost is not None:
            if points_cost < 0:
                raise ValidationError("积分成本不能为负数")
            material.points_cost = points_cost

        if is_featured is not None:
            material.is_featured = is_featured

        # 更新资料
        updated_material = await self.material_repo.update_material(material)

        logger.info(
            "课程资料更新成功",
            material_id=material_id,
        )

        return updated_material

    async def delete_material(
        self,
        material_id: int,
        uploader_id: int,
    ) -> bool:
        """删除课程资料

        Args:
            material_id: 资料ID
            uploader_id: 上传者ID（用于权限验证）

        Returns:
            bool: 是否删除成功

        Raises:
            ResourceNotFoundError: 资料不存在
            PermissionDeniedError: 权限不足
        """
        # 获取资料
        material = await self.material_repo.get_material_by_id(material_id)
        if not material:
            raise ResourceNotFoundError(f"课程资料不存在: {material_id}")

        # 验证权限（只有上传者可以删除）
        if material.uploader_id != uploader_id:
            raise PermissionDeniedError("只有上传者可以删除资料")

        # 删除资料
        await self.material_repo.delete_material(material)

        logger.info(
            "课程资料删除成功",
            material_id=material_id,
        )

        return True

    async def list_materials(
        self,
        course_id: int,
        material_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[CourseMaterial], int]:
        """获取课程资料列表

        Args:
            course_id: 课程ID
            material_type: 资料类型（可选）
            status: 资料状态（可选）
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            Tuple[List[CourseMaterial], int]: 资料列表和总数
        """
        offset = (page - 1) * page_size

        # 验证状态
        status_enum = None
        if status:
            try:
                status_enum = MaterialStatus(status)
            except ValueError:
                raise ValidationError(f"无效的资料状态: {status}")

        # 获取资料列表
        materials = await self.material_repo.search_materials(
            course_id=course_id,
            material_type=material_type,
            status=status_enum,
            offset=offset,
            limit=page_size,
        )

        total = await self.material_repo.count_materials(
            course_id=course_id,
            status=status_enum,
        )

        logger.info(
            "获取课程资料列表",
            course_id=course_id,
            material_type=material_type,
            status=status,
            page=page,
            page_size=page_size,
            count=len(materials),
            total=total,
        )

        return materials, total

    async def approve_material(
        self,
        material_id: int,
        admin_id: int,
    ) -> CourseMaterial:
        """审核通过课程资料

        Args:
            material_id: 资料ID
            admin_id: 管理员ID

        Returns:
            CourseMaterial: 更新后的课程资料对象

        Raises:
            ResourceNotFoundError: 资料不存在
        """
        # 获取资料
        material = await self.material_repo.get_material_by_id(material_id)
        if not material:
            raise ResourceNotFoundError(f"课程资料不存在: {material_id}")

        # 更新状态
        material.status = MaterialStatus.APPROVED

        # 更新资料
        updated_material = await self.material_repo.update_material(material)

        logger.info(
            "课程资料审核通过",
            material_id=material_id,
            admin_id=admin_id,
        )

        return updated_material

    async def reject_material(
        self,
        material_id: int,
        admin_id: int,
        reason: Optional[str] = None,
    ) -> CourseMaterial:
        """审核拒绝课程资料

        Args:
            material_id: 资料ID
            admin_id: 管理员ID
            reason: 拒绝原因

        Returns:
            CourseMaterial: 更新后的课程资料对象

        Raises:
            ResourceNotFoundError: 资料不存在
        """
        # 获取资料
        material = await self.material_repo.get_material_by_id(material_id)
        if not material:
            raise ResourceNotFoundError(f"课程资料不存在: {material_id}")

        # 更新状态
        material.status = MaterialStatus.REJECTED

        # 更新资料
        updated_material = await self.material_repo.update_material(material)

        logger.info(
            "课程资料审核拒绝",
            material_id=material_id,
            admin_id=admin_id,
            reason=reason,
        )

        return updated_material

    async def increment_download_count(
        self,
        material_id: int,
    ) -> CourseMaterial:
        """增加资料下载次数

        Args:
            material_id: 资料ID

        Returns:
            CourseMaterial: 更新后的课程资料对象

        Raises:
            ResourceNotFoundError: 资料不存在
        """
        material = await self.material_repo.increment_download_count(material_id)

        logger.info(
            "资料下载次数增加",
            material_id=material_id,
            download_count=material.download_count,
        )

        return material

    async def get_preview_url(
        self,
        material_id: int,
        user_id: int,
    ) -> tuple[str, str]:
        """获取资料预览URL

        Args:
            material_id: 资料ID
            user_id: 用户ID

        Returns:
            tuple[str, str]: (预览URL, 文件类型)

        Raises:
            ResourceNotFoundError: 资料不存在
            PermissionDeniedError: 资料未审核通过
        """
        # 获取资料
        material = await self.material_repo.get_material_by_id(material_id)
        if not material:
            raise ResourceNotFoundError(f"课程资料不存在: {material_id}")

        # 验证资料状态（只有已审核通过的资料可以预览）
        if material.status != MaterialStatus.APPROVED:
            raise PermissionDeniedError("资料未审核通过，无法预览")

        # 验证文件类型（只支持PDF和图片预览）
        preview_types = ["pdf", "jpg", "jpeg", "png", "gif"]
        file_type = material.file_type.lower() if material.file_type else ""
        if file_type not in preview_types:
            raise ValidationError(f"不支持预览的文件类型: {file_type}")

        # 生成临时预览URL（实际应用中应该使用MinIO的签名URL）
        # 这里使用占位符实现
        preview_url = material.file_url or ""

        return preview_url, file_type


class CoursePostService:
    """课程帖子服务类

    提供课程交流区管理的业务逻辑
    """

    def __init__(
        self,
        post_repository: CoursePostRepository,
        course_repository: CourseRepository,
        audit_engine: Optional[ContentAuditEngine] = None,
    ):
        """初始化服务

        Args:
            post_repository: 帖子仓储
            course_repository: 课程仓储
            audit_engine: 内容审核引擎（可选）
        """
        self.post_repo = post_repository
        self.course_repo = course_repository
        self.audit_engine = audit_engine

    async def create_post(
        self,
        course_id: int,
        user_id: int,
        title: str,
        content: str,
        post_type: str = "discussion",
    ) -> CoursePost:
        """创建帖子

        Args:
            course_id: 课程ID
            user_id: 用户ID
            title: 标题
            content: 内容
            post_type: 类型

        Returns:
            CoursePost: 创建的帖子对象

        Raises:
            ValidationError: 验证失败
            ResourceNotFoundError: 课程不存在
        """
        # 验证课程是否存在
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise ResourceNotFoundError(f"课程不存在: {course_id}")

        # 验证必填字段
        if not title or len(title.strip()) == 0:
            raise ValidationError("标题不能为空")
        if not content or len(content.strip()) == 0:
            raise ValidationError("内容不能为空")

        if len(title) > 200:
            raise ValidationError("标题不能超过200个字符")

        # 内容审核
        if self.audit_engine:
            audit_content = f"{title}\n{content}"
            audit_result = await self.audit_engine.audit_text(
                content=audit_content,
                strict_mode=False,
            )

            if not audit_result.passed:
                logger.warning(
                    "帖子内容审核未通过",
                    course_id=course_id,
                    user_id=user_id,
                    title=title,
                    reason=audit_result.reason,
                    found_words=audit_result.found_words,
                )
                raise ValidationError(f"内容包含敏感词: {audit_result.reason}")

        # 创建帖子
        post = CoursePost(
            course_id=course_id,
            user_id=user_id,
            title=title,
            content=content,
            type=post_type,
        )

        created_post = await self.post_repo.create_post(post)

        logger.info(
            "课程帖子创建成功",
            post_id=created_post.id,
            course_id=course_id,
            user_id=user_id,
            title=title,
        )

        return created_post

    async def list_posts(
        self,
        course_id: int,
        post_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[CoursePost], int]:
        """获取帖子列表

        Args:
            course_id: 课程ID
            post_type: 类型（可选）
            page: 页码
            page_size: 每页数量

        Returns:
            Tuple[List[CoursePost], int]: 帖子列表和总数
        """
        offset = (page - 1) * page_size

        posts = await self.post_repo.list_posts_by_course(
            course_id=course_id,
            post_type=post_type,
            offset=offset,
            limit=page_size,
        )

        total = await self.post_repo.count_posts(
            course_id=course_id,
            post_type=post_type,
        )

        return posts, total
