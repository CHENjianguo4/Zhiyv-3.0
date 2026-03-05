"""课程相关的API端点

提供课程库管理的REST API接口
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, ResourceNotFoundError, PermissionDeniedError
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.course import SchoolService, CourseService, CourseMaterialService, CoursePostService
from app.repositories.course import (
    SchoolRepository,
    CourseRepository,
    CourseMaterialRepository,
    CoursePostRepository,
)
from app.schemas.course import (
    SchoolCreate,
    SchoolUpdate,
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDetailResponse,
    CourseListResponse,
    DepartmentListResponse,
    MaterialCreate,
    MaterialUpdate,
    CoursePostCreate,
    course_to_response,
    course_to_detail_response,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


# ==================== 依赖注入 ====================


async def get_course_service(
    db: AsyncSession = Depends(get_db),
) -> CourseService:
    """获取课程服务实例

    Args:
        db: 数据库会话

    Returns:
        CourseService: 课程服务实例
    """
    course_repo = CourseRepository(db)
    school_repo = SchoolRepository(db)
    return CourseService(course_repo, school_repo)


# ==================== 课程管理接口 ====================


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="创建课程",
    description="创建新的课程信息",
)
async def create_course(
    school_id: int = Query(..., description="学校ID"),
    course_data: CourseCreate = ...,
    service: CourseService = Depends(get_course_service),
):
    """创建课程

    Args:
        school_id: 学校ID
        course_data: 课程创建数据
        service: 课程服务

    Returns:
        创建成功的响应
    """
    try:
        course = await service.create_course(
            school_id=school_id,
            name=course_data.name,
            code=course_data.code,
            department=course_data.department,
            major=course_data.major,
            teacher=course_data.teacher,
            credits=course_data.credits,
            exam_type=course_data.exam_type,
            semester=course_data.semester,
            syllabus=course_data.syllabus,
        )

        return success_response(
            data=course_to_response(course).model_dump(),
            message="课程创建成功",
        )

    except (ValidationError, ResourceNotFoundError) as e:
        logger.warning("创建课程失败", error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error("创建课程时发生错误", error=str(e), exc_info=True)
        return error_response(
            message="创建课程失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/{course_id}",
    response_model=dict,
    summary="获取课程详情",
    description="根据课程ID获取课程详细信息",
)
async def get_course(
    course_id: int,
    load_materials: bool = Query(False, description="是否加载课程资料"),
    service: CourseService = Depends(get_course_service),
):
    """获取课程详情

    Args:
        course_id: 课程ID
        load_materials: 是否加载课程资料
        service: 课程服务

    Returns:
        课程详情响应
    """
    try:
        course = await service.get_course(
            course_id=course_id,
            load_materials=load_materials,
        )

        if load_materials:
            response_data = course_to_detail_response(course).model_dump()
        else:
            response_data = course_to_response(course).model_dump()

        return success_response(
            data=response_data,
            message="获取课程详情成功",
        )

    except ResourceNotFoundError as e:
        logger.warning("获取课程详情失败", course_id=course_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(
            "获取课程详情时发生错误",
            course_id=course_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取课程详情失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put(
    "/{course_id}",
    response_model=dict,
    summary="更新课程信息",
    description="更新指定课程的信息",
)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    service: CourseService = Depends(get_course_service),
):
    """更新课程信息

    Args:
        course_id: 课程ID
        course_data: 课程更新数据
        service: 课程服务

    Returns:
        更新成功的响应
    """
    try:
        course = await service.update_course(
            course_id=course_id,
            name=course_data.name,
            code=course_data.code,
            department=course_data.department,
            major=course_data.major,
            teacher=course_data.teacher,
            credits=course_data.credits,
            exam_type=course_data.exam_type,
            semester=course_data.semester,
            syllabus=course_data.syllabus,
        )

        return success_response(
            data=course_to_response(course).model_dump(),
            message="课程更新成功",
        )

    except (ValidationError, ResourceNotFoundError) as e:
        logger.warning("更新课程失败", course_id=course_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(
            "更新课程时发生错误",
            course_id=course_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="更新课程失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.delete(
    "/{course_id}",
    response_model=dict,
    summary="删除课程",
    description="删除指定的课程",
)
async def delete_course(
    course_id: int,
    service: CourseService = Depends(get_course_service),
):
    """删除课程

    Args:
        course_id: 课程ID
        service: 课程服务

    Returns:
        删除成功的响应
    """
    try:
        await service.delete_course(course_id=course_id)

        return success_response(
            data={"course_id": course_id},
            message="课程删除成功",
        )

    except ResourceNotFoundError as e:
        logger.warning("删除课程失败", course_id=course_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(
            "删除课程时发生错误",
            course_id=course_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="删除课程失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "",
    response_model=dict,
    summary="获取课程列表/搜索课程",
    description="获取课程列表，支持按学校、院系筛选和关键词搜索",
)
async def list_courses(
    school_id: int = Query(..., description="学校ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词（课程名称或代码）"),
    department: Optional[str] = Query(None, description="院系"),
    teacher: Optional[str] = Query(None, description="教师姓名"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: CourseService = Depends(get_course_service),
):
    """获取课程列表或搜索课程

    Args:
        school_id: 学校ID
        keyword: 搜索关键词
        department: 院系
        teacher: 教师姓名
        page: 页码
        page_size: 每页数量
        service: 课程服务

    Returns:
        课程列表响应
    """
    try:
        # 如果有关键词或教师筛选，使用搜索功能
        if keyword or teacher:
            courses, total = await service.search_courses(
                school_id=school_id,
                keyword=keyword,
                department=department,
                teacher=teacher,
                page=page,
                page_size=page_size,
            )
        else:
            # 否则使用普通列表查询
            courses, total = await service.list_courses(
                school_id=school_id,
                department=department,
                page=page,
                page_size=page_size,
            )

        response_data = CourseListResponse(
            courses=[course_to_response(c) for c in courses],
            total=total,
            page=page,
            page_size=page_size,
        )

        return success_response(
            data=response_data.model_dump(),
            message="获取课程列表成功",
        )

    except Exception as e:
        logger.error(
            "获取课程列表时发生错误",
            school_id=school_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取课程列表失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/schools/{school_id}/departments",
    response_model=dict,
    summary="获取学校院系列表",
    description="获取指定学校的所有院系列表",
)
async def list_departments(
    school_id: int,
    service: CourseService = Depends(get_course_service),
):
    """获取学校院系列表

    Args:
        school_id: 学校ID
        service: 课程服务

    Returns:
        院系列表响应
    """
    try:
        departments = await service.list_departments(school_id=school_id)

        response_data = DepartmentListResponse(departments=departments)

        return success_response(
            data=response_data.model_dump(),
            message="获取院系列表成功",
        )

    except Exception as e:
        logger.error(
            "获取院系列表时发生错误",
            school_id=school_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取院系列表失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



# ==================== 课程资料管理接口 ====================


async def get_material_service(
    db: AsyncSession = Depends(get_db),
) -> "CourseMaterialService":
    """获取课程资料服务实例

    Args:
        db: 数据库会话

    Returns:
        CourseMaterialService: 课程资料服务实例
    """
    from app.services.course import CourseMaterialService
    from app.repositories.course import CourseMaterialRepository, CourseRepository
    
    material_repo = CourseMaterialRepository(db)
    course_repo = CourseRepository(db)
    
    # TODO: 集成内容审核引擎
    return CourseMaterialService(material_repo, course_repo, audit_engine=None)


@router.post(
    "/{course_id}/materials",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="上传课程资料",
    description="上传课程资料，支持文件类型和下载权限设置",
)
async def upload_material(
    course_id: int,
    material_data: MaterialCreate,
    current_user: User = Depends(get_current_user),
    service: "CourseMaterialService" = Depends(get_material_service),
):
    """上传课程资料

    Args:
        course_id: 课程ID
        material_data: 资料创建数据
        current_user: 当前登录用户
        service: 课程资料服务

    Returns:
        创建成功的响应
    """
    from app.schemas.course import material_to_response

    try:
        material = await service.create_material(
            course_id=course_id,
            uploader_id=current_user.id,
            name=material_data.name,
            material_type=material_data.type,
            file_url=material_data.file_url,
            file_size=material_data.file_size,
            file_type=material_data.file_type,
            description=material_data.description,
            download_permission=material_data.download_permission,
            points_cost=material_data.points_cost,
        )

        return success_response(
            data=material_to_response(material).model_dump(),
            message="课程资料上传成功",
        )

    except (ValidationError, ResourceNotFoundError) as e:
        logger.warning("上传课程资料失败", course_id=course_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(
            "上传课程资料时发生错误",
            course_id=course_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="上传课程资料失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/{course_id}/materials",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="上传课程资料",
    description="为指定课程上传学习资料",
)
async def upload_material(
    course_id: int,
    material_data: "MaterialCreate",
    uploader_id: int = Query(..., description="上传者ID"),
    service: "CourseMaterialService" = Depends(get_material_service),
):
    """上传课程资料

    Args:
        course_id: 课程ID
        material_data: 资料创建数据
        uploader_id: 上传者ID
        service: 课程资料服务

    Returns:
        创建成功的响应
    """
    from app.schemas.course import material_to_response
    
    try:
        material = await service.create_material(
            course_id=course_id,
            uploader_id=uploader_id,
            name=material_data.name,
            material_type=material_data.type,
            file_url=material_data.file_url,
            file_size=material_data.file_size,
            file_type=material_data.file_type,
            description=material_data.description,
            download_permission=material_data.download_permission,
            points_cost=material_data.points_cost,
        )

        return success_response(
            data=material_to_response(material).model_dump(),
            message="课程资料上传成功",
        )

    except (ValidationError, ResourceNotFoundError) as e:
        logger.warning("上传课程资料失败", course_id=course_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(
            "上传课程资料时发生错误",
            course_id=course_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="上传课程资料失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/{course_id}/materials",
    response_model=dict,
    summary="获取课程资料列表",
    description="获取指定课程的资料列表",
)
async def list_materials(
    course_id: int,
    material_type: Optional[str] = Query(None, description="资料类型"),
    status_filter: Optional[str] = Query(None, alias="status", description="资料状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: "CourseMaterialService" = Depends(get_material_service),
):
    """获取课程资料列表

    Args:
        course_id: 课程ID
        material_type: 资料类型
        status_filter: 资料状态
        page: 页码
        page_size: 每页数量
        service: 课程资料服务

    Returns:
        资料列表响应
    """
    from app.schemas.course import MaterialListResponse, material_to_response
    
    try:
        materials, total = await service.list_materials(
            course_id=course_id,
            material_type=material_type,
            status=status_filter,
            page=page,
            page_size=page_size,
        )

        response_data = MaterialListResponse(
            materials=[material_to_response(m) for m in materials],
            total=total,
            page=page,
            page_size=page_size,
        )

        return success_response(
            data=response_data.model_dump(),
            message="获取课程资料列表成功",
        )

    except ValidationError as e:
        logger.warning("获取课程资料列表失败", course_id=course_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(
            "获取课程资料列表时发生错误",
            course_id=course_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取课程资料列表失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/materials/{material_id}",
    response_model=dict,
    summary="获取资料详情",
    description="获取指定资料的详细信息",
)
async def get_material(
    material_id: int,
    service: "CourseMaterialService" = Depends(get_material_service),
):
    """获取资料详情

    Args:
        material_id: 资料ID
        service: 课程资料服务

    Returns:
        资料详情响应
    """
    from app.schemas.course import material_to_response
    
    try:
        material = await service.get_material(material_id)

        return success_response(
            data=material_to_response(material).model_dump(),
            message="获取资料详情成功",
        )

    except ResourceNotFoundError as e:
        logger.warning("获取资料详情失败", material_id=material_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(
            "获取资料详情时发生错误",
            material_id=material_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取资料详情失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.put(
    "/materials/{material_id}",
    response_model=dict,
    summary="更新资料信息",
    description="更新指定资料的信息",
)
async def update_material(
    material_id: int,
    material_data: "MaterialUpdate",
    uploader_id: int = Query(..., description="上传者ID"),
    service: "CourseMaterialService" = Depends(get_material_service),
):
    """更新资料信息

    Args:
        material_id: 资料ID
        material_data: 资料更新数据
        uploader_id: 上传者ID
        service: 课程资料服务

    Returns:
        更新成功的响应
    """
    from app.schemas.course import material_to_response
    
    try:
        material = await service.update_material(
            material_id=material_id,
            uploader_id=uploader_id,
            name=material_data.name,
            description=material_data.description,
            download_permission=material_data.download_permission,
            points_cost=material_data.points_cost,
            is_featured=material_data.is_featured,
        )

        return success_response(
            data=material_to_response(material).model_dump(),
            message="资料更新成功",
        )

    except (ValidationError, ResourceNotFoundError, PermissionDeniedError) as e:
        logger.warning("更新资料失败", material_id=material_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(
            "更新资料时发生错误",
            material_id=material_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="更新资料失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.delete(
    "/materials/{material_id}",
    response_model=dict,
    summary="删除资料",
    description="删除指定的资料",
)
async def delete_material(
    material_id: int,
    uploader_id: int = Query(..., description="上传者ID"),
    service: "CourseMaterialService" = Depends(get_material_service),
):
    """删除资料

    Args:
        material_id: 资料ID
        uploader_id: 上传者ID
        service: 课程资料服务

    Returns:
        删除成功的响应
    """
    try:
        await service.delete_material(
            material_id=material_id,
            uploader_id=uploader_id,
        )

        return success_response(
            data={"material_id": material_id},
            message="资料删除成功",
        )

    except (ResourceNotFoundError, PermissionDeniedError) as e:
        logger.warning("删除资料失败", material_id=material_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(
            "删除资料时发生错误",
            material_id=material_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="删除资料失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/materials/upload",
    response_model=dict,
    summary="上传文件（占位符）",
    description="上传文件到MinIO对象存储（占位符实现）",
)
async def upload_file():
    """上传文件（占位符）

    这是一个占位符接口，实际实现需要集成MinIO对象存储服务。

    Returns:
        上传成功的响应，包含文件URL
    """
    # TODO: 集成MinIO对象存储
    # 1. 接收文件上传
    # 2. 验证文件类型和大小
    # 3. 上传到MinIO
    # 4. 返回文件URL

    return success_response(
        data={
            "file_url": "https://example.com/files/placeholder.pdf",
            "file_size": 1024000,
            "file_type": "pdf",
        },
        message="文件上传成功（占位符）",
    )


@router.get(
    "/materials/{material_id}/download-url",
    response_model=dict,
    summary="获取临时下载URL",
    description="获取临时下载URL（不扣除积分，仅用于已支付用户）",
)
async def get_download_url(
    material_id: int,
    user_id: int = Query(..., description="用户ID"),
    service: "CourseMaterialService" = Depends(get_material_service),
):
    """获取临时下载URL

    这个接口用于已经支付过积分的用户重新获取下载链接，不会再次扣除积分。
    实际应用中应该记录用户的下载历史来判断是否已支付。

    Args:
        material_id: 资料ID
        user_id: 用户ID
        service: 课程资料服务

    Returns:
        下载URL响应
    """
    from app.schemas.course import MaterialDownloadResponse
    
    try:
        # 获取资料
        material = await service.get_material(material_id)

        # 验证资料状态
        if material.status.value != "approved":
            return error_response(
                message="资料未审核通过，无法下载",
                code=status.HTTP_403_FORBIDDEN,
            )

        # 生成临时下载URL（不扣除积分）
        # TODO: 实际应用中应该检查用户是否已经下载过此资料
        download_url = material.file_url or ""
        expires_in = 3600  # 1小时过期

        response_data = MaterialDownloadResponse(
            download_url=download_url,
            expires_in=expires_in,
        )

        logger.info(
            "获取临时下载URL",
            material_id=material_id,
            user_id=user_id,
        )

        return success_response(
            data=response_data.model_dump(),
            message="获取下载URL成功",
        )

    except ResourceNotFoundError as e:
        logger.warning("获取下载URL失败", material_id=material_id, error=str(e))
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(
            "获取下载URL时发生错误",
            material_id=material_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取下载URL失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/materials/{material_id}/download",
    response_model=dict,
    summary="下载资料",
    description="下载资料（带积分兑换逻辑）",
)
async def download_material(
    material_id: int,
    user_id: int = Query(..., description="用户ID"),
    service: "CourseMaterialService" = Depends(get_material_service),
    db: AsyncSession = Depends(get_db),
):
    """下载资料

    Args:
        material_id: 资料ID
        user_id: 用户ID
        service: 课程资料服务
        db: 数据库会话

    Returns:
        下载URL响应
    """
    from app.schemas.course import MaterialDownloadResponse
    from app.repositories.user import UserRepository
    
    try:
        # 创建用户仓储
        user_repo = UserRepository(db)
        
        # 获取下载URL（包含积分扣除逻辑）
        download_url, expires_in = await service.get_download_url(
            material_id=material_id,
            user_id=user_id,
            user_repository=user_repo,
        )

        response_data = MaterialDownloadResponse(
            download_url=download_url,
            expires_in=expires_in,
        )

        return success_response(
            data=response_data.model_dump(),
            message="获取下载URL成功",
        )

    except (ResourceNotFoundError, PermissionDeniedError) as e:
        logger.warning("获取下载URL失败", material_id=material_id, error=str(e))
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else status.HTTP_403_FORBIDDEN
        return error_response(
            message=str(e),
            code=code,
        )
    except Exception as e:
        logger.error(
            "获取下载URL时发生错误",
            material_id=material_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取下载URL失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/materials/{material_id}/preview",
    response_model=dict,
    summary="获取资料预览URL",
    description="获取资料在线预览URL（支持PDF和图片）",
)
async def get_material_preview(
    material_id: int,
    user_id: int = Query(..., description="用户ID"),
    service: "CourseMaterialService" = Depends(get_material_service),
):
    """获取资料预览URL

    Args:
        material_id: 资料ID
        user_id: 用户ID
        service: 课程资料服务

    Returns:
        预览URL响应
    """
    from app.schemas.course import MaterialPreviewResponse
    
    try:
        preview_url, file_type = await service.get_preview_url(
            material_id=material_id,
            user_id=user_id,
        )

        response_data = MaterialPreviewResponse(
            preview_url=preview_url,
            file_type=file_type,
        )

        return success_response(
            data=response_data.model_dump(),
            message="获取预览URL成功",
        )

    except (ResourceNotFoundError, PermissionDeniedError, ValidationError) as e:
        logger.warning("获取预览URL失败", material_id=material_id, error=str(e))
        code = status.HTTP_400_BAD_REQUEST if isinstance(e, ValidationError) else (
            status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else status.HTTP_403_FORBIDDEN
        )
        return error_response(
            message=str(e),
            code=code,
        )
    except Exception as e:
        logger.error(
            "获取预览URL时发生错误",
            material_id=material_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取预览URL失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==================== 课程帖子管理接口 ====================


async def get_post_service(
    db: AsyncSession = Depends(get_db),
) -> CoursePostService:
    """获取课程帖子服务实例"""
    post_repo = CoursePostRepository(db)
    course_repo = CourseRepository(db)
    # TODO: 集成内容审核引擎
    return CoursePostService(post_repo, course_repo, audit_engine=None)


@router.post(
    "/{course_id}/posts",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="发布课程帖子",
    description="在课程交流区发布帖子",
)
async def create_course_post(
    course_id: int,
    post_data: CoursePostCreate,
    current_user: User = Depends(get_current_user),
    service: CoursePostService = Depends(get_post_service),
):
    """发布课程帖子

    Args:
        course_id: 课程ID
        post_data: 帖子创建数据
        current_user: 当前登录用户
        service: 课程帖子服务

    Returns:
        创建成功的响应
    """
    from app.schemas.course import post_to_response

    try:
        post = await service.create_post(
            course_id=course_id,
            user_id=current_user.id,
            title=post_data.title,
            content=post_data.content,
            post_type=post_data.type,
        )

        return success_response(
            data=post_to_response(post).model_dump(),
            message="帖子发布成功",
        )

    except (ValidationError, ResourceNotFoundError) as e:
        logger.warning("发布帖子失败", course_id=course_id, error=str(e))
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else status.HTTP_400_BAD_REQUEST
        return error_response(
            message=str(e),
            code=code,
        )
    except Exception as e:
        logger.error(
            "发布帖子时发生错误",
            course_id=course_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="发布帖子失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/{course_id}/posts",
    response_model=dict,
    summary="获取课程帖子列表",
    description="获取课程交流区帖子列表，支持分页和类型筛选",
)
async def list_course_posts(
    course_id: int,
    type: str = Query(None, description="帖子类型(discussion/question/resource)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: CoursePostService = Depends(get_post_service),
):
    """获取课程帖子列表

    Args:
        course_id: 课程ID
        type: 帖子类型
        page: 页码
        page_size: 每页数量
        service: 课程帖子服务

    Returns:
        帖子列表响应
    """
    from app.schemas.course import post_to_response, CoursePostListResponse

    try:
        posts, total = await service.list_posts(
            course_id=course_id,
            post_type=type,
            page=page,
            page_size=page_size,
        )

        response_data = CoursePostListResponse(
            posts=[post_to_response(p) for p in posts],
            total=total,
            page=page,
            page_size=page_size,
        )

        return success_response(
            data=response_data.model_dump(),
            message="获取帖子列表成功",
        )

    except Exception as e:
        logger.error(
            "获取帖子列表时发生错误",
            course_id=course_id,
            error=str(e),
            exc_info=True,
        )
        return error_response(
            message="获取帖子列表失败",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
