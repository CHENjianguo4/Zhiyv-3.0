"""课程仓储层

提供课程相关的数据访问操作
"""

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import (
    School,
    SchoolStatus,
    Course,
    CourseMaterial,
    MaterialStatus,
    CoursePost,
)


class SchoolRepository:
    """学校仓储类

    提供学校的CRUD操作
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    async def create_school(self, school: School) -> School:
        """创建学校

        Args:
            school: 学校对象

        Returns:
            School: 创建后的学校对象（包含ID）
        """
        self.session.add(school)
        await self.session.flush()
        await self.session.refresh(school)
        return school

    async def get_school_by_id(self, school_id: int) -> Optional[School]:
        """根据ID获取学校

        Args:
            school_id: 学校ID

        Returns:
            Optional[School]: 学校对象，不存在则返回None
        """
        query = select(School).where(School.id == school_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_school_by_name(self, name: str) -> Optional[School]:
        """根据名称获取学校

        Args:
            name: 学校名称

        Returns:
            Optional[School]: 学校对象，不存在则返回None
        """
        query = select(School).where(School.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_school(self, school: School) -> School:
        """更新学校

        Args:
            school: 学校对象

        Returns:
            School: 更新后的学校对象
        """
        await self.session.flush()
        await self.session.refresh(school)
        return school

    async def delete_school(self, school: School) -> None:
        """删除学校

        Args:
            school: 学校对象
        """
        await self.session.delete(school)
        await self.session.flush()

    async def list_active_schools(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> list[School]:
        """获取活跃学校列表

        Args:
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[School]: 学校列表
        """
        query = (
            select(School)
            .where(School.status == SchoolStatus.ACTIVE)
            .order_by(School.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_schools(self, status: Optional[SchoolStatus] = None) -> int:
        """统计学校数量

        Args:
            status: 学校状态（可选）

        Returns:
            int: 学校数量
        """
        query = select(func.count(School.id))
        if status is not None:
            query = query.where(School.status == status)
        result = await self.session.execute(query)
        return result.scalar_one()


class CourseRepository:
    """课程仓储类

    提供课程的CRUD操作和查询功能
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    async def create_course(self, course: Course) -> Course:
        """创建课程

        Args:
            course: 课程对象

        Returns:
            Course: 创建后的课程对象（包含ID）
        """
        self.session.add(course)
        await self.session.flush()
        await self.session.refresh(course)
        return course

    async def get_course_by_id(
        self,
        course_id: int,
        load_materials: bool = False,
    ) -> Optional[Course]:
        """根据ID获取课程

        Args:
            course_id: 课程ID
            load_materials: 是否加载课程资料

        Returns:
            Optional[Course]: 课程对象，不存在则返回None
        """
        query = select(Course).where(Course.id == course_id)

        if load_materials:
            query = query.options(selectinload(Course.materials))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_course_by_code(
        self,
        school_id: int,
        code: str,
    ) -> Optional[Course]:
        """根据学校ID和课程代码获取课程

        Args:
            school_id: 学校ID
            code: 课程代码

        Returns:
            Optional[Course]: 课程对象，不存在则返回None
        """
        query = select(Course).where(
            Course.school_id == school_id,
            Course.code == code,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_course(self, course: Course) -> Course:
        """更新课程

        Args:
            course: 课程对象

        Returns:
            Course: 更新后的课程对象
        """
        await self.session.flush()
        await self.session.refresh(course)
        return course

    async def delete_course(self, course: Course) -> None:
        """删除课程

        Args:
            course: 课程对象
        """
        await self.session.delete(course)
        await self.session.flush()

    async def list_courses_by_school(
        self,
        school_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Course]:
        """根据学校ID获取课程列表

        Args:
            school_id: 学校ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[Course]: 课程列表
        """
        query = (
            select(Course)
            .where(Course.school_id == school_id)
            .order_by(Course.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_courses_by_department(
        self,
        school_id: int,
        department: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Course]:
        """根据学校ID和院系获取课程列表

        Args:
            school_id: 学校ID
            department: 院系
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[Course]: 课程列表
        """
        query = (
            select(Course)
            .where(
                Course.school_id == school_id,
                Course.department == department,
            )
            .order_by(Course.name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search_courses(
        self,
        school_id: int,
        keyword: Optional[str] = None,
        department: Optional[str] = None,
        teacher: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Course]:
        """搜索课程

        Args:
            school_id: 学校ID
            keyword: 关键词（搜索课程名称和代码）
            department: 院系
            teacher: 教师
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[Course]: 课程列表
        """
        query = select(Course).where(Course.school_id == school_id)

        if keyword:
            query = query.where(
                (Course.name.contains(keyword)) | (Course.code.contains(keyword))
            )

        if department:
            query = query.where(Course.department == department)

        if teacher:
            query = query.where(Course.teacher.contains(teacher))

        query = query.order_by(Course.name).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_courses(
        self,
        school_id: int,
        department: Optional[str] = None,
    ) -> int:
        """统计课程数量

        Args:
            school_id: 学校ID
            department: 院系（可选）

        Returns:
            int: 课程数量
        """
        query = select(func.count(Course.id)).where(Course.school_id == school_id)

        if department:
            query = query.where(Course.department == department)

        result = await self.session.execute(query)
        return result.scalar_one()


class CourseMaterialRepository:
    """课程资料仓储类

    提供课程资料的CRUD操作和查询功能
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    async def create_material(self, material: CourseMaterial) -> CourseMaterial:
        """创建课程资料

        Args:
            material: 课程资料对象

        Returns:
            CourseMaterial: 创建后的课程资料对象（包含ID）
        """
        self.session.add(material)
        await self.session.flush()
        await self.session.refresh(material)
        return material

    async def get_material_by_id(
        self,
        material_id: int,
    ) -> Optional[CourseMaterial]:
        """根据ID获取课程资料

        Args:
            material_id: 资料ID

        Returns:
            Optional[CourseMaterial]: 课程资料对象，不存在则返回None
        """
        query = select(CourseMaterial).where(CourseMaterial.id == material_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_material(self, material: CourseMaterial) -> CourseMaterial:
        """更新课程资料

        Args:
            material: 课程资料对象

        Returns:
            CourseMaterial: 更新后的课程资料对象
        """
        await self.session.flush()
        await self.session.refresh(material)
        return material

    async def delete_material(self, material: CourseMaterial) -> None:
        """删除课程资料

        Args:
            material: 课程资料对象
        """
        await self.session.delete(material)
        await self.session.flush()

    async def list_materials_by_course(
        self,
        course_id: int,
        status: Optional[MaterialStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[CourseMaterial]:
        """根据课程ID获取资料列表

        Args:
            course_id: 课程ID
            status: 资料状态（可选）
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[CourseMaterial]: 课程资料列表
        """
        query = select(CourseMaterial).where(CourseMaterial.course_id == course_id)

        if status is not None:
            query = query.where(CourseMaterial.status == status)

        query = (
            query.order_by(CourseMaterial.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_materials_by_uploader(
        self,
        uploader_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[CourseMaterial]:
        """根据上传者ID获取资料列表

        Args:
            uploader_id: 上传者ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[CourseMaterial]: 课程资料列表
        """
        query = (
            select(CourseMaterial)
            .where(CourseMaterial.uploader_id == uploader_id)
            .order_by(CourseMaterial.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search_materials(
        self,
        course_id: int,
        keyword: Optional[str] = None,
        material_type: Optional[str] = None,
        status: Optional[MaterialStatus] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[CourseMaterial]:
        """搜索课程资料

        Args:
            course_id: 课程ID
            keyword: 关键词（搜索资料名称）
            material_type: 资料类型
            status: 资料状态
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[CourseMaterial]: 课程资料列表
        """
        query = select(CourseMaterial).where(CourseMaterial.course_id == course_id)

        if keyword:
            query = query.where(CourseMaterial.name.contains(keyword))

        if material_type:
            query = query.where(CourseMaterial.type == material_type)

        if status is not None:
            query = query.where(CourseMaterial.status == status)

        query = (
            query.order_by(CourseMaterial.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def increment_download_count(self, material_id: int) -> CourseMaterial:
        """增加资料下载次数

        Args:
            material_id: 资料ID

        Returns:
            CourseMaterial: 更新后的课程资料对象

        Raises:
            ValueError: 资料不存在
        """
        material = await self.get_material_by_id(material_id)
        if material is None:
            raise ValueError(f"课程资料不存在: {material_id}")

        material.download_count += 1
        await self.update_material(material)

        return material

    async def count_materials(
        self,
        course_id: int,
        status: Optional[MaterialStatus] = None,
    ) -> int:
        """统计课程资料数量

        Args:
            course_id: 课程ID
            status: 资料状态（可选）

        Returns:
            int: 资料数量
        """
        query = select(func.count(CourseMaterial.id)).where(
            CourseMaterial.course_id == course_id
        )

        if status is not None:
            query = query.where(CourseMaterial.status == status)

        result = await self.session.execute(query)
        return result.scalar_one()


class CoursePostRepository:
    """课程帖子仓储类

    提供课程帖子的CRUD操作和查询功能
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    async def create_post(self, post: CoursePost) -> CoursePost:
        """创建帖子

        Args:
            post: 帖子对象

        Returns:
            CoursePost: 创建后的帖子对象（包含ID）
        """
        self.session.add(post)
        await self.session.flush()
        await self.session.refresh(post)
        return post

    async def get_post_by_id(self, post_id: int) -> Optional[CoursePost]:
        """根据ID获取帖子

        Args:
            post_id: 帖子ID

        Returns:
            Optional[CoursePost]: 帖子对象，不存在则返回None
        """
        query = select(CoursePost).where(CoursePost.id == post_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_posts_by_course(
        self,
        course_id: int,
        post_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[CoursePost]:
        """根据课程ID获取帖子列表

        Args:
            course_id: 课程ID
            post_type: 帖子类型（可选）
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[CoursePost]: 帖子列表
        """
        query = select(CoursePost).where(CoursePost.course_id == course_id)

        if post_type:
            query = query.where(CoursePost.type == post_type)

        # 排序：置顶优先，然后按创建时间倒序
        query = (
            query.order_by(CoursePost.is_pinned.desc(), CoursePost.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_posts(
        self,
        course_id: int,
        post_type: Optional[str] = None,
    ) -> int:
        """统计帖子数量

        Args:
            course_id: 课程ID
            post_type: 帖子类型（可选）

        Returns:
            int: 帖子数量
        """
        query = select(func.count(CoursePost.id)).where(CoursePost.course_id == course_id)

        if post_type:
            query = query.where(CoursePost.type == post_type)

        result = await self.session.execute(query)
        return result.scalar_one()
