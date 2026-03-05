"""课程资料下载与预览功能测试

测试资料下载、预览、积分兑换等功能
"""

import pytest
from decimal import Decimal

from app.models.course import (
    CourseMaterial,
    MaterialType,
    MaterialStatus,
    DownloadPermission,
)
from app.models.user import User, UserRole, UserStatus
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
)


@pytest.mark.asyncio
class TestMaterialPreview:
    """测试资料预览功能"""

    async def test_get_preview_url_for_pdf(
        self,
        material_service,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试获取PDF资料预览URL"""
        # 创建PDF资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="测试课件.pdf",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/test.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.FREE,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 获取预览URL
        preview_url, file_type = await material_service.get_preview_url(
            material_id=material.id,
            user_id=sample_user.id,
        )

        # 验证
        assert preview_url == "https://example.com/files/test.pdf"
        assert file_type == "pdf"

    async def test_get_preview_url_for_image(
        self,
        material_service,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试获取图片资料预览URL"""
        # 创建图片资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="测试图片.jpg",
            type=MaterialType.NOTES,
            file_url="https://example.com/files/test.jpg",
            file_type="jpg",
            download_permission=DownloadPermission.FREE,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 获取预览URL
        preview_url, file_type = await material_service.get_preview_url(
            material_id=material.id,
            user_id=sample_user.id,
        )

        # 验证
        assert preview_url == "https://example.com/files/test.jpg"
        assert file_type == "jpg"

    async def test_preview_unapproved_material_fails(
        self,
        material_service,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试预览未审核资料失败"""
        # 创建未审核资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="待审核资料.pdf",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/test.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.FREE,
            status=MaterialStatus.PENDING,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 尝试预览应该失败
        with pytest.raises(PermissionDeniedError, match="资料未审核通过"):
            await material_service.get_preview_url(
                material_id=material.id,
                user_id=sample_user.id,
            )

    async def test_preview_unsupported_file_type_fails(
        self,
        material_service,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试预览不支持的文件类型失败"""
        # 创建Word文档资料（不支持预览）
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="测试文档.docx",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/test.docx",
            file_type="docx",
            download_permission=DownloadPermission.FREE,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 尝试预览应该失败
        with pytest.raises(ValidationError, match="不支持在线预览"):
            await material_service.get_preview_url(
                material_id=material.id,
                user_id=sample_user.id,
            )

    async def test_preview_nonexistent_material_fails(
        self,
        material_service,
        sample_user,
    ):
        """测试预览不存在的资料失败"""
        with pytest.raises(ResourceNotFoundError, match="课程资料不存在"):
            await material_service.get_preview_url(
                material_id=99999,
                user_id=sample_user.id,
            )


@pytest.mark.asyncio
class TestMaterialDownload:
    """测试资料下载功能"""

    async def test_download_free_material(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试下载免费资料"""
        # 创建免费资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="免费资料.pdf",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/free.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.FREE,
            points_cost=0,
            download_count=0,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 记录初始积分
        initial_points = sample_user.points

        # 下载资料
        download_url, expires_in = await material_service.get_download_url(
            material_id=material.id,
            user_id=sample_user.id,
            user_repository=user_repository,
        )

        # 验证
        assert download_url == "https://example.com/files/free.pdf"
        assert expires_in == 3600

        # 刷新资料和用户
        await db_session.refresh(material)
        await db_session.refresh(sample_user)

        # 验证下载计数增加
        assert material.download_count == 1

        # 验证积分未扣除
        assert sample_user.points == initial_points

    async def test_download_points_material_with_sufficient_points(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试下载积分资料（积分充足）"""
        # 设置用户积分
        sample_user.points = 100
        await db_session.commit()

        # 创建积分资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="积分资料.pdf",
            type=MaterialType.EXAM,
            file_url="https://example.com/files/points.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.POINTS,
            points_cost=10,
            download_count=0,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 下载资料
        download_url, expires_in = await material_service.get_download_url(
            material_id=material.id,
            user_id=sample_user.id,
            user_repository=user_repository,
        )

        # 验证
        assert download_url == "https://example.com/files/points.pdf"
        assert expires_in == 3600

        # 刷新资料和用户
        await db_session.refresh(material)
        await db_session.refresh(sample_user)

        # 验证下载计数增加
        assert material.download_count == 1

        # 验证积分扣除
        assert sample_user.points == 90

        # 验证积分记录
        point_logs = await user_repository.get_point_logs(sample_user.id)
        assert len(point_logs) > 0
        latest_log = point_logs[0]
        assert latest_log.change_amount == -10
        assert latest_log.action_type == "material_download"
        assert "下载资料" in latest_log.description

    async def test_download_points_material_with_insufficient_points(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试下载积分资料（积分不足）"""
        # 设置用户积分不足
        sample_user.points = 5
        await db_session.commit()

        # 创建积分资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="积分资料.pdf",
            type=MaterialType.EXAM,
            file_url="https://example.com/files/points.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.POINTS,
            points_cost=10,
            download_count=0,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 尝试下载应该失败
        with pytest.raises(PermissionDeniedError, match="积分不足"):
            await material_service.get_download_url(
                material_id=material.id,
                user_id=sample_user.id,
                user_repository=user_repository,
            )

        # 刷新资料和用户
        await db_session.refresh(material)
        await db_session.refresh(sample_user)

        # 验证下载计数未增加
        assert material.download_count == 0

        # 验证积分未扣除
        assert sample_user.points == 5

    async def test_download_unapproved_material_fails(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试下载未审核资料失败"""
        # 创建未审核资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="待审核资料.pdf",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/test.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.FREE,
            status=MaterialStatus.PENDING,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 尝试下载应该失败
        with pytest.raises(PermissionDeniedError, match="资料未审核通过"):
            await material_service.get_download_url(
                material_id=material.id,
                user_id=sample_user.id,
                user_repository=user_repository,
            )

    async def test_download_nonexistent_material_fails(
        self,
        material_service,
        user_repository,
        sample_user,
    ):
        """测试下载不存在的资料失败"""
        with pytest.raises(ResourceNotFoundError, match="课程资料不存在"):
            await material_service.get_download_url(
                material_id=99999,
                user_id=sample_user.id,
                user_repository=user_repository,
            )

    async def test_download_with_nonexistent_user_fails(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试不存在的用户下载资料失败"""
        # 创建资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="测试资料.pdf",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/test.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.FREE,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 尝试用不存在的用户下载
        with pytest.raises(ResourceNotFoundError, match="用户不存在"):
            await material_service.get_download_url(
                material_id=material.id,
                user_id=99999,
                user_repository=user_repository,
            )


@pytest.mark.asyncio
class TestDownloadCount:
    """测试下载计数功能"""

    async def test_download_count_increments(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试下载计数递增"""
        # 创建资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="测试资料.pdf",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/test.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.FREE,
            download_count=0,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 多次下载
        for i in range(3):
            await material_service.get_download_url(
                material_id=material.id,
                user_id=sample_user.id,
                user_repository=user_repository,
            )

            # 刷新并验证计数
            await db_session.refresh(material)
            assert material.download_count == i + 1

    async def test_multiple_users_download_increments_count(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_school,
        db_session,
    ):
        """测试多个用户下载增加计数"""
        # 创建多个用户
        users = []
        for i in range(3):
            user = User(
                wechat_openid=f"test_openid_{i}",
                school_id=sample_school.id,
                nickname=f"测试用户{i}",
                verified=True,
                points=100,
            )
            db_session.add(user)
            users.append(user)
        await db_session.commit()

        # 创建资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=users[0].id,
            name="测试资料.pdf",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/test.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.FREE,
            download_count=0,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 每个用户下载一次
        for user in users:
            await material_service.get_download_url(
                material_id=material.id,
                user_id=user.id,
                user_repository=user_repository,
            )

        # 验证计数
        await db_session.refresh(material)
        assert material.download_count == 3


@pytest.mark.asyncio
class TestPointsExchange:
    """测试积分兑换逻辑"""

    async def test_points_deduction_for_paid_material(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试付费资料扣除积分"""
        # 设置用户积分
        sample_user.points = 50
        await db_session.commit()

        # 创建不同积分成本的资料
        materials = []
        for cost in [5, 10, 15]:
            material = CourseMaterial(
                course_id=sample_course.id,
                uploader_id=sample_user.id,
                name=f"资料{cost}积分.pdf",
                type=MaterialType.EXAM,
                file_url=f"https://example.com/files/test{cost}.pdf",
                file_type="pdf",
                download_permission=DownloadPermission.POINTS,
                points_cost=cost,
                status=MaterialStatus.APPROVED,
            )
            db_session.add(material)
            materials.append(material)
        await db_session.commit()

        # 依次下载资料
        expected_points = 50
        for material in materials:
            await db_session.refresh(material)
            await material_service.get_download_url(
                material_id=material.id,
                user_id=sample_user.id,
                user_repository=user_repository,
            )

            # 验证积分扣除
            await db_session.refresh(sample_user)
            expected_points -= material.points_cost
            assert sample_user.points == expected_points

        # 最终积分应该是 50 - 5 - 10 - 15 = 20
        assert sample_user.points == 20

    async def test_points_not_deducted_for_free_material(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试免费资料不扣除积分"""
        # 设置用户积分
        initial_points = 50
        sample_user.points = initial_points
        await db_session.commit()

        # 创建免费资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="免费资料.pdf",
            type=MaterialType.COURSEWARE,
            file_url="https://example.com/files/free.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.FREE,
            points_cost=0,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 下载资料
        await material_service.get_download_url(
            material_id=material.id,
            user_id=sample_user.id,
            user_repository=user_repository,
        )

        # 验证积分未扣除
        await db_session.refresh(sample_user)
        assert sample_user.points == initial_points

    async def test_point_log_created_on_download(
        self,
        material_service,
        user_repository,
        sample_course,
        sample_user,
        db_session,
    ):
        """测试下载时创建积分记录"""
        # 设置用户积分
        sample_user.points = 100
        await db_session.commit()

        # 创建积分资料
        material = CourseMaterial(
            course_id=sample_course.id,
            uploader_id=sample_user.id,
            name="积分资料.pdf",
            type=MaterialType.EXAM,
            file_url="https://example.com/files/points.pdf",
            file_type="pdf",
            download_permission=DownloadPermission.POINTS,
            points_cost=20,
            status=MaterialStatus.APPROVED,
        )
        db_session.add(material)
        await db_session.commit()
        await db_session.refresh(material)

        # 下载资料
        await material_service.get_download_url(
            material_id=material.id,
            user_id=sample_user.id,
            user_repository=user_repository,
        )

        # 验证积分记录
        point_logs = await user_repository.get_point_logs(sample_user.id)
        assert len(point_logs) > 0

        latest_log = point_logs[0]
        assert latest_log.user_id == sample_user.id
        assert latest_log.change_amount == -20
        assert latest_log.action_type == "material_download"
        assert material.name in latest_log.description
