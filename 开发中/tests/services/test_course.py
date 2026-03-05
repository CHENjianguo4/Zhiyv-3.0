"""课程服务测试

测试课程库管理功能，包括课程CRUD、搜索、层级查询等
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.course import SchoolService, CourseService
from app.repositories.course import (
    SchoolRepository,
    CourseRepository,
    CourseMaterialRepository,
)
from app.models.course import (
    School,
    SchoolStatus,
    Course,
    CourseMaterial,
    ExamType,
    MaterialType,
    MaterialStatus,
    DownloadPermission,
)
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
)


# ==================== Fixtures ====================


@pytest.fixture
def mock_school_repo():
    """模拟学校仓储"""
    return AsyncMock(spec=SchoolRepository)


@pytest.fixture
def mock_course_repo():
    """模拟课程仓储"""
    return AsyncMock(spec=CourseRepository)


@pytest.fixture
def mock_material_repo():
    """模拟课程资料仓储"""
    return AsyncMock(spec=CourseMaterialRepository)


@pytest.fixture
def school_service(mock_school_repo):
    """创建学校服务实例"""
    return SchoolService(mock_school_repo)


@pytest.fixture
def course_service(mock_course_repo, mock_school_repo):
    """创建课程服务实例"""
    return CourseService(mock_course_repo, mock_school_repo)


@pytest.fixture
def sample_school():
    """示例学校数据"""
    return School(
        id=1,
        name="测试大学",
        short_name="测大",
        province="北京市",
        city="北京市",
        logo="https://example.com/logo.png",
        status=SchoolStatus.ACTIVE,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_course():
    """示例课程数据"""
    return Course(
        id=1,
        school_id=1,
        code="CS101",
        name="计算机科学导论",
        department="计算机学院",
        major="计算机科学与技术",
        teacher="张三",
        credits=Decimal("3.0"),
        exam_type=ExamType.EXAM,
        semester="2024春季",
        syllabus="课程大纲内容...",
        rating_count=10,
        avg_rating=Decimal("4.5"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_material():
    """示例课程资料数据"""
    return CourseMaterial(
        id=1,
        course_id=1,
        uploader_id=1,
        name="第一章课件",
        type=MaterialType.COURSEWARE,
        file_url="https://example.com/material.pdf",
        file_size=1024000,
        file_type="pdf",
        description="第一章的课件内容",
        download_permission=DownloadPermission.FREE,
        points_cost=0,
        download_count=50,
        is_featured=True,
        status=MaterialStatus.APPROVED,
        created_at=datetime.utcnow(),
    )


# ==================== 学校服务测试 ====================


@pytest.mark.asyncio
async def test_create_school_success(school_service, mock_school_repo, sample_school):
    """测试成功创建学校"""
    # 模拟学校名称不存在
    mock_school_repo.get_school_by_name.return_value = None
    mock_school_repo.create_school.return_value = sample_school
    
    # 执行创建
    result = await school_service.create_school(
        name="测试大学",
        short_name="测大",
        province="北京市",
        city="北京市",
        logo="https://example.com/logo.png",
    )
    
    # 验证结果
    assert result.id == 1
    assert result.name == "测试大学"
    assert result.short_name == "测大"
    assert result.status == SchoolStatus.ACTIVE
    
    # 验证调用
    mock_school_repo.get_school_by_name.assert_called_once_with("测试大学")
    mock_school_repo.create_school.assert_called_once()


@pytest.mark.asyncio
async def test_create_school_empty_name(school_service):
    """测试创建学校时名称为空"""
    with pytest.raises(ValidationError) as exc_info:
        await school_service.create_school(name="")
    
    assert "学校名称不能为空" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_school_duplicate_name(school_service, mock_school_repo, sample_school):
    """测试创建学校时名称重复"""
    # 模拟学校名称已存在
    mock_school_repo.get_school_by_name.return_value = sample_school
    
    with pytest.raises(ValidationError) as exc_info:
        await school_service.create_school(name="测试大学")
    
    assert "学校名称已存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_school_success(school_service, mock_school_repo, sample_school):
    """测试成功获取学校信息"""
    mock_school_repo.get_school_by_id.return_value = sample_school
    
    result = await school_service.get_school(school_id=1)
    
    assert result.id == 1
    assert result.name == "测试大学"
    mock_school_repo.get_school_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_school_not_found(school_service, mock_school_repo):
    """测试获取不存在的学校"""
    mock_school_repo.get_school_by_id.return_value = None
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        await school_service.get_school(school_id=999)
    
    assert "学校不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_schools(school_service, mock_school_repo, sample_school):
    """测试获取学校列表"""
    mock_school_repo.list_active_schools.return_value = [sample_school]
    mock_school_repo.count_schools.return_value = 1
    
    schools, total = await school_service.list_schools(page=1, page_size=20)
    
    assert len(schools) == 1
    assert total == 1
    assert schools[0].name == "测试大学"
    
    mock_school_repo.list_active_schools.assert_called_once_with(offset=0, limit=20)
    mock_school_repo.count_schools.assert_called_once()


# ==================== 课程服务测试 ====================


@pytest.mark.asyncio
async def test_create_course_success(
    course_service,
    mock_course_repo,
    mock_school_repo,
    sample_school,
    sample_course,
):
    """测试成功创建课程"""
    # 模拟学校存在
    mock_school_repo.get_school_by_id.return_value = sample_school
    # 模拟课程代码不存在
    mock_course_repo.get_course_by_code.return_value = None
    mock_course_repo.create_course.return_value = sample_course
    
    # 执行创建
    result = await course_service.create_course(
        school_id=1,
        name="计算机科学导论",
        code="CS101",
        department="计算机学院",
        major="计算机科学与技术",
        teacher="张三",
        credits=Decimal("3.0"),
        exam_type="exam",
        semester="2024春季",
        syllabus="课程大纲内容...",
    )
    
    # 验证结果
    assert result.id == 1
    assert result.name == "计算机科学导论"
    assert result.code == "CS101"
    assert result.teacher == "张三"
    assert result.credits == Decimal("3.0")
    
    # 验证调用
    mock_school_repo.get_school_by_id.assert_called_once_with(1)
    mock_course_repo.get_course_by_code.assert_called_once_with(
        school_id=1, code="CS101"
    )
    mock_course_repo.create_course.assert_called_once()


@pytest.mark.asyncio
async def test_create_course_school_not_found(course_service, mock_school_repo):
    """测试创建课程时学校不存在"""
    mock_school_repo.get_school_by_id.return_value = None
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        await course_service.create_course(
            school_id=999,
            name="测试课程",
        )
    
    assert "学校不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_course_empty_name(
    course_service,
    mock_school_repo,
    sample_school,
):
    """测试创建课程时名称为空"""
    mock_school_repo.get_school_by_id.return_value = sample_school
    
    with pytest.raises(ValidationError) as exc_info:
        await course_service.create_course(
            school_id=1,
            name="",
        )
    
    assert "课程名称不能为空" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_course_duplicate_code(
    course_service,
    mock_course_repo,
    mock_school_repo,
    sample_school,
    sample_course,
):
    """测试创建课程时代码重复"""
    mock_school_repo.get_school_by_id.return_value = sample_school
    mock_course_repo.get_course_by_code.return_value = sample_course
    
    with pytest.raises(ValidationError) as exc_info:
        await course_service.create_course(
            school_id=1,
            name="新课程",
            code="CS101",
        )
    
    assert "课程代码已存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_course_invalid_exam_type(
    course_service,
    mock_school_repo,
    sample_school,
):
    """测试创建课程时考核方式无效"""
    mock_school_repo.get_school_by_id.return_value = sample_school
    
    with pytest.raises(ValidationError) as exc_info:
        await course_service.create_course(
            school_id=1,
            name="测试课程",
            exam_type="invalid_type",
        )
    
    assert "无效的考核方式" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_course_success(course_service, mock_course_repo, sample_course):
    """测试成功获取课程详情"""
    mock_course_repo.get_course_by_id.return_value = sample_course
    
    result = await course_service.get_course(course_id=1, load_materials=False)
    
    assert result.id == 1
    assert result.name == "计算机科学导论"
    mock_course_repo.get_course_by_id.assert_called_once_with(
        course_id=1, load_materials=False
    )


@pytest.mark.asyncio
async def test_get_course_with_materials(
    course_service,
    mock_course_repo,
    sample_course,
    sample_material,
):
    """测试获取课程详情（包含资料）"""
    # 添加资料到课程
    sample_course.materials = [sample_material]
    mock_course_repo.get_course_by_id.return_value = sample_course
    
    result = await course_service.get_course(course_id=1, load_materials=True)
    
    assert result.id == 1
    assert len(result.materials) == 1
    assert result.materials[0].name == "第一章课件"
    mock_course_repo.get_course_by_id.assert_called_once_with(
        course_id=1, load_materials=True
    )


@pytest.mark.asyncio
async def test_get_course_not_found(course_service, mock_course_repo):
    """测试获取不存在的课程"""
    mock_course_repo.get_course_by_id.return_value = None
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        await course_service.get_course(course_id=999)
    
    assert "课程不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_course_success(
    course_service,
    mock_course_repo,
    sample_course,
):
    """测试成功更新课程"""
    mock_course_repo.get_course_by_id.return_value = sample_course
    mock_course_repo.update_course.return_value = sample_course
    
    result = await course_service.update_course(
        course_id=1,
        name="更新后的课程名称",
        teacher="李四",
    )
    
    assert result.id == 1
    mock_course_repo.get_course_by_id.assert_called_once_with(1)
    mock_course_repo.update_course.assert_called_once()


@pytest.mark.asyncio
async def test_update_course_not_found(course_service, mock_course_repo):
    """测试更新不存在的课程"""
    mock_course_repo.get_course_by_id.return_value = None
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        await course_service.update_course(
            course_id=999,
            name="新名称",
        )
    
    assert "课程不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_delete_course_success(course_service, mock_course_repo, sample_course):
    """测试成功删除课程"""
    mock_course_repo.get_course_by_id.return_value = sample_course
    mock_course_repo.delete_course.return_value = None
    
    result = await course_service.delete_course(course_id=1)
    
    assert result is True
    mock_course_repo.get_course_by_id.assert_called_once_with(1)
    mock_course_repo.delete_course.assert_called_once_with(sample_course)


@pytest.mark.asyncio
async def test_delete_course_not_found(course_service, mock_course_repo):
    """测试删除不存在的课程"""
    mock_course_repo.get_course_by_id.return_value = None
    
    with pytest.raises(ResourceNotFoundError) as exc_info:
        await course_service.delete_course(course_id=999)
    
    assert "课程不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_courses_by_school(
    course_service,
    mock_course_repo,
    sample_course,
):
    """测试按学校获取课程列表"""
    mock_course_repo.list_courses_by_school.return_value = [sample_course]
    mock_course_repo.count_courses.return_value = 1
    
    courses, total = await course_service.list_courses(
        school_id=1,
        page=1,
        page_size=20,
    )
    
    assert len(courses) == 1
    assert total == 1
    assert courses[0].name == "计算机科学导论"
    
    mock_course_repo.list_courses_by_school.assert_called_once_with(
        school_id=1,
        offset=0,
        limit=20,
    )
    mock_course_repo.count_courses.assert_called_once_with(
        school_id=1,
        department=None,
    )


@pytest.mark.asyncio
async def test_list_courses_by_department(
    course_service,
    mock_course_repo,
    sample_course,
):
    """测试按院系获取课程列表"""
    mock_course_repo.list_courses_by_department.return_value = [sample_course]
    mock_course_repo.count_courses.return_value = 1
    
    courses, total = await course_service.list_courses(
        school_id=1,
        department="计算机学院",
        page=1,
        page_size=20,
    )
    
    assert len(courses) == 1
    assert total == 1
    assert courses[0].department == "计算机学院"
    
    mock_course_repo.list_courses_by_department.assert_called_once_with(
        school_id=1,
        department="计算机学院",
        offset=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_search_courses_by_keyword(
    course_service,
    mock_course_repo,
    sample_course,
):
    """测试按关键词搜索课程"""
    mock_course_repo.search_courses.return_value = [sample_course]
    
    courses, total = await course_service.search_courses(
        school_id=1,
        keyword="计算机",
        page=1,
        page_size=20,
    )
    
    assert len(courses) == 1
    assert "计算机" in courses[0].name
    
    mock_course_repo.search_courses.assert_called_once_with(
        school_id=1,
        keyword="计算机",
        department=None,
        teacher=None,
        offset=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_search_courses_by_teacher(
    course_service,
    mock_course_repo,
    sample_course,
):
    """测试按教师搜索课程"""
    mock_course_repo.search_courses.return_value = [sample_course]
    
    courses, total = await course_service.search_courses(
        school_id=1,
        teacher="张三",
        page=1,
        page_size=20,
    )
    
    assert len(courses) == 1
    assert courses[0].teacher == "张三"
    
    mock_course_repo.search_courses.assert_called_once_with(
        school_id=1,
        keyword=None,
        department=None,
        teacher="张三",
        offset=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_search_courses_combined_filters(
    course_service,
    mock_course_repo,
    sample_course,
):
    """测试组合条件搜索课程"""
    mock_course_repo.search_courses.return_value = [sample_course]
    
    courses, total = await course_service.search_courses(
        school_id=1,
        keyword="计算机",
        department="计算机学院",
        teacher="张三",
        page=1,
        page_size=20,
    )
    
    assert len(courses) == 1
    
    mock_course_repo.search_courses.assert_called_once_with(
        school_id=1,
        keyword="计算机",
        department="计算机学院",
        teacher="张三",
        offset=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_list_departments(course_service, mock_course_repo, sample_course):
    """测试获取院系列表"""
    # 创建多个不同院系的课程
    course1 = Course(
        id=1,
        school_id=1,
        name="课程1",
        department="计算机学院",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    course2 = Course(
        id=2,
        school_id=1,
        name="课程2",
        department="数学学院",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    course3 = Course(
        id=3,
        school_id=1,
        name="课程3",
        department="计算机学院",  # 重复院系
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    mock_course_repo.list_courses_by_school.return_value = [course1, course2, course3]
    
    departments = await course_service.list_departments(school_id=1)
    
    # 验证结果：应该去重并排序
    assert len(departments) == 2
    assert "计算机学院" in departments
    assert "数学学院" in departments
    assert departments == sorted(departments)  # 验证已排序
    
    mock_course_repo.list_courses_by_school.assert_called_once_with(
        school_id=1,
        offset=0,
        limit=10000,
    )


@pytest.mark.asyncio
async def test_pagination_calculation(course_service, mock_course_repo, sample_course):
    """测试分页计算"""
    mock_course_repo.list_courses_by_school.return_value = [sample_course]
    mock_course_repo.count_courses.return_value = 100
    
    # 测试第3页，每页20条
    courses, total = await course_service.list_courses(
        school_id=1,
        page=3,
        page_size=20,
    )
    
    # 验证offset计算正确：(3-1) * 20 = 40
    mock_course_repo.list_courses_by_school.assert_called_once_with(
        school_id=1,
        offset=40,
        limit=20,
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
