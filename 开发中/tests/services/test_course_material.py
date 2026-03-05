"""
Tests for Course Material Service

Tests the course material upload and management functionality.
"""
import pytest
from decimal import Decimal

from app.services.course import CourseMaterialService
from app.repositories.course import CourseMaterialRepository, CourseRepository
from app.models.course import (
    Course,
    CourseMaterial,
    MaterialType,
    MaterialStatus,
    DownloadPermission,
)
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
)


@pytest.mark.asyncio
class TestCourseMaterialService:
    """Test course material service"""

    async def test_create_material_success(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test creating a course material successfully"""
        # Create a course first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
            code="TEST101",
            department="计算机学院",
            teacher="张老师",
        )
        course = await course_repo.create_course(course)
        await db_session.commit()

        # Create material
        material_repo = CourseMaterialRepository(db_session)
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)

        material = await service.create_material(
            course_id=course.id,
            uploader_id=test_user.id,
            name="课程PPT",
            material_type="courseware",
            file_url="https://example.com/files/test.pdf",
            file_size=1024000,
            file_type="pdf",
            description="第一章课件",
            download_permission="free",
            points_cost=0,
        )
        await db_session.commit()

        assert material.id is not None
        assert material.course_id == course.id
        assert material.uploader_id == test_user.id
        assert material.name == "课程PPT"
        assert material.type == MaterialType.COURSEWARE
        assert material.file_url == "https://example.com/files/test.pdf"
        assert material.file_size == 1024000
        assert material.file_type == "pdf"
        assert material.description == "第一章课件"
        assert material.download_permission == DownloadPermission.FREE
        assert material.points_cost == 0
        assert material.status == MaterialStatus.APPROVED
        assert material.download_count == 0

    async def test_create_material_with_points(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test creating a material with points requirement"""
        # Create a course first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
            code="TEST102",
        )
        course = await course_repo.create_course(course)
        await db_session.commit()

        # Create material with points
        material_repo = CourseMaterialRepository(db_session)
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)

        material = await service.create_material(
            course_id=course.id,
            uploader_id=test_user.id,
            name="历年真题",
            material_type="exam",
            file_url="https://example.com/files/exam.pdf",
            file_size=512000,
            file_type="pdf",
            description="2020-2023年真题合集",
            download_permission="points",
            points_cost=10,
        )
        await db_session.commit()

        assert material.download_permission == DownloadPermission.POINTS
        assert material.points_cost == 10

    async def test_create_material_invalid_course(
        self,
        db_session,
        test_user,
    ):
        """Test creating material for non-existent course"""
        course_repo = CourseRepository(db_session)
        material_repo = CourseMaterialRepository(db_session)
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await service.create_material(
                course_id=99999,
                uploader_id=test_user.id,
                name="测试资料",
                material_type="courseware",
            )

        assert "课程不存在" in str(exc_info.value)

    async def test_create_material_empty_name(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test creating material with empty name"""
        # Create a course first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)
        await db_session.commit()

        material_repo = CourseMaterialRepository(db_session)
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_material(
                course_id=course.id,
                uploader_id=test_user.id,
                name="",
                material_type="courseware",
            )

        assert "资料名称不能为空" in str(exc_info.value)

    async def test_create_material_invalid_type(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test creating material with invalid type"""
        # Create a course first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)
        await db_session.commit()

        material_repo = CourseMaterialRepository(db_session)
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_material(
                course_id=course.id,
                uploader_id=test_user.id,
                name="测试资料",
                material_type="invalid_type",
            )

        assert "无效的资料类型" in str(exc_info.value)

    async def test_create_material_invalid_file_type(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test creating material with unsupported file type"""
        # Create a course first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)
        await db_session.commit()

        material_repo = CourseMaterialRepository(db_session)
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_material(
                course_id=course.id,
                uploader_id=test_user.id,
                name="测试资料",
                material_type="courseware",
                file_type="exe",
            )

        assert "不支持的文件类型" in str(exc_info.value)

    async def test_create_material_points_without_cost(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test creating points material without setting cost"""
        # Create a course first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)
        await db_session.commit()

        material_repo = CourseMaterialRepository(db_session)
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)

        with pytest.raises(ValidationError) as exc_info:
            await service.create_material(
                course_id=course.id,
                uploader_id=test_user.id,
                name="测试资料",
                material_type="courseware",
                download_permission="points",
                points_cost=0,
            )

        assert "积分兑换资料必须设置积分成本" in str(exc_info.value)

    async def test_update_material_success(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test updating material successfully"""
        # Create a course and material first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)

        material_repo = CourseMaterialRepository(db_session)
        material = CourseMaterial(
            course_id=course.id,
            uploader_id=test_user.id,
            name="原始名称",
            type=MaterialType.COURSEWARE,
            download_permission=DownloadPermission.FREE,
            points_cost=0,
        )
        material = await material_repo.create_material(material)
        await db_session.commit()

        # Update material
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)
        updated_material = await service.update_material(
            material_id=material.id,
            uploader_id=test_user.id,
            name="更新后的名称",
            description="新的描述",
            download_permission="points",
            points_cost=5,
        )
        await db_session.commit()

        assert updated_material.name == "更新后的名称"
        assert updated_material.description == "新的描述"
        assert updated_material.download_permission == DownloadPermission.POINTS
        assert updated_material.points_cost == 5

    async def test_update_material_permission_denied(
        self,
        db_session,
        test_school,
        test_user,
        test_user_2,
    ):
        """Test updating material by non-owner"""
        # Create a course and material first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)

        material_repo = CourseMaterialRepository(db_session)
        material = CourseMaterial(
            course_id=course.id,
            uploader_id=test_user.id,
            name="原始名称",
            type=MaterialType.COURSEWARE,
            download_permission=DownloadPermission.FREE,
            points_cost=0,
        )
        material = await material_repo.create_material(material)
        await db_session.commit()

        # Try to update by another user
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)
        with pytest.raises(PermissionDeniedError) as exc_info:
            await service.update_material(
                material_id=material.id,
                uploader_id=test_user_2.id,
                name="尝试更新",
            )

        assert "只有上传者可以修改资料" in str(exc_info.value)

    async def test_delete_material_success(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test deleting material successfully"""
        # Create a course and material first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)

        material_repo = CourseMaterialRepository(db_session)
        material = CourseMaterial(
            course_id=course.id,
            uploader_id=test_user.id,
            name="待删除资料",
            type=MaterialType.COURSEWARE,
            download_permission=DownloadPermission.FREE,
            points_cost=0,
        )
        material = await material_repo.create_material(material)
        await db_session.commit()

        material_id = material.id

        # Delete material
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)
        result = await service.delete_material(
            material_id=material_id,
            uploader_id=test_user.id,
        )
        await db_session.commit()

        assert result is True

        # Verify material is deleted
        deleted_material = await material_repo.get_material_by_id(material_id)
        assert deleted_material is None

    async def test_list_materials(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test listing materials for a course"""
        # Create a course first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)

        # Create multiple materials
        material_repo = CourseMaterialRepository(db_session)
        for i in range(5):
            material = CourseMaterial(
                course_id=course.id,
                uploader_id=test_user.id,
                name=f"资料{i+1}",
                type=MaterialType.COURSEWARE,
                download_permission=DownloadPermission.FREE,
                points_cost=0,
            )
            await material_repo.create_material(material)
        await db_session.commit()

        # List materials
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)
        materials, total = await service.list_materials(
            course_id=course.id,
            page=1,
            page_size=10,
        )

        assert len(materials) == 5
        assert total == 5

    async def test_increment_download_count(
        self,
        db_session,
        test_school,
        test_user,
    ):
        """Test incrementing download count"""
        # Create a course and material first
        course_repo = CourseRepository(db_session)
        course = Course(
            school_id=test_school.id,
            name="测试课程",
        )
        course = await course_repo.create_course(course)

        material_repo = CourseMaterialRepository(db_session)
        material = CourseMaterial(
            course_id=course.id,
            uploader_id=test_user.id,
            name="测试资料",
            type=MaterialType.COURSEWARE,
            download_permission=DownloadPermission.FREE,
            points_cost=0,
        )
        material = await material_repo.create_material(material)
        await db_session.commit()

        initial_count = material.download_count

        # Increment download count
        service = CourseMaterialService(material_repo, course_repo, audit_engine=None)
        updated_material = await service.increment_download_count(material.id)
        await db_session.commit()

        assert updated_material.download_count == initial_count + 1
