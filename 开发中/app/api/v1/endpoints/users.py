"""用户相关API端点

提供用户档案查询、更新等接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_mysql_session
from app.core.response import success_response
from app.repositories.user import UserRepository
from app.schemas.user import (
    CreditScoreResponse,
    PointsResponse,
    UpdateProfileRequest,
    UserProfileDTO,
)
from app.services.credit import get_credit_service

router = APIRouter(prefix="/users", tags=["用户"])


# ==================== API端点 ====================


@router.get(
    "/{user_id}",
    response_model=UserProfileDTO,
    status_code=status.HTTP_200_OK,
    summary="获取用户档案",
    description="""
    获取用户的完整档案信息。
    
    - 返回脱敏后的隐私信息（学号、手机号、邮箱等）
    - 数据库保留完整信息
    - 仅用于展示，不可用于验证
    """,
)
async def get_user_profile(
    user_id: int,
    session: AsyncSession = Depends(get_mysql_session),
):
    """获取用户档案
    
    Args:
        user_id: 用户ID
        session: 数据库会话
        
    Returns:
        用户档案信息（脱敏后）
        
    Raises:
        HTTPException: 用户不存在时返回404
    """
    repo = UserRepository(session)
    
    # 获取用户信息（包含档案）
    user = await repo.get_user_by_id(user_id, load_profile=True)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在: {user_id}",
        )
    
    # 转换为DTO（自动应用脱敏）
    profile_dto = UserProfileDTO.from_user(user, user.profile)
    
    return success_response(
        data=profile_dto,
        message="获取用户档案成功",
    )


@router.put(
    "/{user_id}/profile",
    response_model=UserProfileDTO,
    status_code=status.HTTP_200_OK,
    summary="更新用户档案",
    description="""
    更新用户的档案信息。
    
    - 可更新昵称、头像、年级、专业、校区、标签、简介
    - 不可更新学号、真实姓名等认证信息
    - 返回更新后的档案信息（脱敏）
    """,
)
async def update_user_profile(
    user_id: int,
    request: UpdateProfileRequest,
    session: AsyncSession = Depends(get_mysql_session),
):
    """更新用户档案
    
    Args:
        user_id: 用户ID
        request: 更新请求数据
        session: 数据库会话
        
    Returns:
        更新后的用户档案信息（脱敏后）
        
    Raises:
        HTTPException: 用户不存在时返回404
    """
    repo = UserRepository(session)
    
    # 获取用户信息
    user = await repo.get_user_by_id(user_id, load_profile=True)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在: {user_id}",
        )
    
    # 更新用户基本信息
    if request.nickname is not None:
        user.nickname = request.nickname
    if request.avatar is not None:
        user.avatar = request.avatar
    
    await repo.update_user(user)
    
    # 更新或创建用户档案
    profile = user.profile
    if profile is None:
        from app.models.user import UserProfile
        
        profile = UserProfile(user_id=user_id)
        await repo.create_profile(profile)
    
    # 更新档案信息
    if request.grade is not None:
        profile.grade = request.grade
    if request.major is not None:
        profile.major = request.major
    if request.campus is not None:
        profile.campus = request.campus
    if request.tags is not None:
        profile.tags = {"tags": request.tags}
    if request.bio is not None:
        profile.bio = request.bio
    
    await repo.update_profile(profile)
    await session.commit()
    
    # 刷新数据
    await session.refresh(user)
    await session.refresh(profile)
    
    # 转换为DTO（自动应用脱敏）
    profile_dto = UserProfileDTO.from_user(user, profile)
    
    return success_response(
        data=profile_dto,
        message="更新用户档案成功",
    )


@router.get(
    "/{user_id}/credit",
    response_model=CreditScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="查询信用分",
    description="""
    查询用户的信用分和变更历史。
    
    - 返回当前信用分
    - 返回最近的信用分变更记录
    - 支持分页查询历史记录
    """,
)
async def get_credit_score(
    user_id: int,
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_mysql_session),
):
    """查询信用分
    
    Args:
        user_id: 用户ID
        offset: 偏移量
        limit: 限制数量
        session: 数据库会话
        
    Returns:
        信用分和变更历史
        
    Raises:
        HTTPException: 用户不存在时返回404
    """
    repo = UserRepository(session)
    
    # 获取用户信息
    user = await repo.get_user_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在: {user_id}",
        )
    
    # 获取信用分变更历史
    logs = await repo.get_credit_logs_by_user_id(user_id, offset, limit)
    
    from app.schemas.user import CreditLogDTO
    
    response = CreditScoreResponse(
        score=user.credit_score,
        history=[CreditLogDTO.model_validate(log) for log in logs],
    )
    
    return success_response(
        data=response,
        message="查询信用分成功",
    )


@router.get(
    "/{user_id}/points",
    response_model=PointsResponse,
    status_code=status.HTTP_200_OK,
    summary="查询积分",
    description="""
    查询用户的积分和变更历史。
    
    - 返回当前积分
    - 返回最近的积分变更记录
    - 支持分页查询历史记录
    """,
)
async def get_points(
    user_id: int,
    offset: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_mysql_session),
):
    """查询积分
    
    Args:
        user_id: 用户ID
        offset: 偏移量
        limit: 限制数量
        session: 数据库会话
        
    Returns:
        积分和变更历史
        
    Raises:
        HTTPException: 用户不存在时返回404
    """
    repo = UserRepository(session)
    
    # 获取用户信息
    user = await repo.get_user_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在: {user_id}",
        )
    
    # 获取积分变更历史
    logs = await repo.get_point_logs_by_user_id(user_id, offset, limit)
    
    from app.schemas.user import PointLogDTO
    
    response = PointsResponse(
        points=user.points,
        history=[PointLogDTO.model_validate(log) for log in logs],
    )
    
    return success_response(
        data=response,
        message="查询积分成功",
    )



@router.post(
    "/{user_id}/credit/increase",
    response_model=CreditScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="增加信用分",
    description="""
    增加用户的信用分。
    
    - 需要提供变更原因
    - 可选关联对象类型和ID
    - 信用分上限为100分
    - 自动记录变更历史
    """,
)
async def increase_credit_score(
    user_id: int,
    request: "ChangeCreditScoreRequest",
    session: AsyncSession = Depends(get_mysql_session),
):
    """增加信用分
    
    Args:
        user_id: 用户ID
        request: 变更请求数据
        session: 数据库会话
        
    Returns:
        更新后的信用分和变更历史
        
    Raises:
        HTTPException: 用户不存在或参数无效时
    """
    from app.core.exceptions import BusinessException
    from app.schemas.user import ChangeCreditScoreRequest
    
    credit_service = get_credit_service(session)
    
    try:
        # 增加信用分
        user, log = await credit_service.increase_credit_score(
            user_id=user_id,
            amount=request.amount,
            reason=request.reason,
            related_type=request.related_type,
            related_id=request.related_id,
        )
        
        await session.commit()
        
        # 获取最新的信用分历史
        repo = UserRepository(session)
        logs = await repo.get_credit_logs_by_user_id(user_id, offset=0, limit=20)
        
        from app.schemas.user import CreditLogDTO
        
        response = CreditScoreResponse(
            score=user.credit_score,
            history=[CreditLogDTO.model_validate(log) for log in logs],
        )
        
        return success_response(
            data=response,
            message=f"增加信用分成功，当前信用分：{user.credit_score}",
        )
        
    except BusinessException as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"增加信用分失败: {str(e)}",
        ) from e


@router.post(
    "/{user_id}/credit/decrease",
    response_model=CreditScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="扣除信用分",
    description="""
    扣除用户的信用分。
    
    - 需要提供变更原因
    - 可选关联对象类型和ID
    - 信用分下限为0分
    - 自动记录变更历史
    - 信用分低于60分将限制部分功能
    - 信用分低于30分将禁止交易和发布功能
    """,
)
async def decrease_credit_score(
    user_id: int,
    request: "ChangeCreditScoreRequest",
    session: AsyncSession = Depends(get_mysql_session),
):
    """扣除信用分
    
    Args:
        user_id: 用户ID
        request: 变更请求数据
        session: 数据库会话
        
    Returns:
        更新后的信用分和变更历史
        
    Raises:
        HTTPException: 用户不存在或参数无效时
    """
    from app.core.exceptions import BusinessException
    from app.schemas.user import ChangeCreditScoreRequest
    
    credit_service = get_credit_service(session)
    
    try:
        # 扣除信用分
        user, log = await credit_service.decrease_credit_score(
            user_id=user_id,
            amount=request.amount,
            reason=request.reason,
            related_type=request.related_type,
            related_id=request.related_id,
        )
        
        await session.commit()
        
        # 获取最新的信用分历史
        repo = UserRepository(session)
        logs = await repo.get_credit_logs_by_user_id(user_id, offset=0, limit=20)
        
        from app.schemas.user import CreditLogDTO
        
        response = CreditScoreResponse(
            score=user.credit_score,
            history=[CreditLogDTO.model_validate(log) for log in logs],
        )
        
        return success_response(
            data=response,
            message=f"扣除信用分成功，当前信用分：{user.credit_score}",
        )
        
    except BusinessException as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"扣除信用分失败: {str(e)}",
        ) from e


@router.get(
    "/{user_id}/credit/permissions",
    status_code=status.HTTP_200_OK,
    summary="检查信用分权限",
    description="""
    检查用户基于信用分的权限。
    
    根据需求3.3和3.4：
    - 信用分低于60分：限制接单、发布和交易权限
    - 信用分低于30分：禁止所有交易和发布功能
    
    返回各项权限的布尔值。
    """,
)
async def check_credit_permissions(
    user_id: int,
    session: AsyncSession = Depends(get_mysql_session),
):
    """检查信用分权限
    
    Args:
        user_id: 用户ID
        session: 数据库会话
        
    Returns:
        权限字典
        
    Raises:
        HTTPException: 用户不存在时
    """
    from app.core.exceptions import BusinessException
    
    credit_service = get_credit_service(session)
    
    try:
        permissions = await credit_service.check_credit_permissions(user_id)
        
        return success_response(
            data=permissions,
            message="查询权限成功",
        )
        
    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        ) from e


# ==================== 兴趣标签管理 ====================


@router.post(
    "/{user_id}/profile/tags",
    response_model=UserProfileDTO,
    status_code=status.HTTP_200_OK,
    summary="添加兴趣标签",
    description="""
    为用户添加兴趣标签。
    
    - 支持批量添加多个标签
    - 自动去重，不会添加重复标签
    - 返回更新后的用户档案
    """,
)
async def add_interest_tags(
    user_id: int,
    request: "AddTagsRequest",
    session: AsyncSession = Depends(get_mysql_session),
):
    """添加兴趣标签
    
    Args:
        user_id: 用户ID
        request: 添加标签请求
        session: 数据库会话
        
    Returns:
        更新后的用户档案
        
    Raises:
        HTTPException: 用户不存在时
    """
    from app.schemas.user import AddTagsRequest
    
    repo = UserRepository(session)
    
    # 获取用户和档案
    user = await repo.get_user_by_id(user_id, load_profile=True)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在: {user_id}",
        )
    
    # 获取或创建档案
    profile = user.profile
    if profile is None:
        from app.models.user import UserProfile
        
        profile = UserProfile(user_id=user_id)
        await repo.create_profile(profile)
    
    # 获取现有标签
    existing_tags = []
    if profile.tags and isinstance(profile.tags, dict) and "tags" in profile.tags:
        existing_tags = profile.tags["tags"]
    elif profile.tags and isinstance(profile.tags, list):
        existing_tags = profile.tags
    
    # 添加新标签（去重）
    existing_tags_set = set(existing_tags)
    for tag in request.tags:
        existing_tags_set.add(tag)
    
    # 更新标签
    profile.tags = {"tags": list(existing_tags_set)}
    await repo.update_profile(profile)
    await session.commit()
    
    # 刷新数据
    await session.refresh(user)
    await session.refresh(profile)
    
    # 转换为DTO
    profile_dto = UserProfileDTO.from_user(user, profile)
    
    return success_response(
        data=profile_dto,
        message=f"成功添加 {len(request.tags)} 个标签",
    )


@router.delete(
    "/{user_id}/profile/tags",
    response_model=UserProfileDTO,
    status_code=status.HTTP_200_OK,
    summary="删除兴趣标签",
    description="""
    删除用户的兴趣标签。
    
    - 支持批量删除多个标签
    - 如果标签不存在，不会报错
    - 返回更新后的用户档案
    """,
)
async def remove_interest_tags(
    user_id: int,
    request: "RemoveTagsRequest",
    session: AsyncSession = Depends(get_mysql_session),
):
    """删除兴趣标签
    
    Args:
        user_id: 用户ID
        request: 删除标签请求
        session: 数据库会话
        
    Returns:
        更新后的用户档案
        
    Raises:
        HTTPException: 用户不存在时
    """
    from app.schemas.user import RemoveTagsRequest
    
    repo = UserRepository(session)
    
    # 获取用户和档案
    user = await repo.get_user_by_id(user_id, load_profile=True)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在: {user_id}",
        )
    
    # 获取档案
    profile = user.profile
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户档案不存在: {user_id}",
        )
    
    # 获取现有标签
    existing_tags = []
    if profile.tags and isinstance(profile.tags, dict) and "tags" in profile.tags:
        existing_tags = profile.tags["tags"]
    elif profile.tags and isinstance(profile.tags, list):
        existing_tags = profile.tags
    
    # 删除指定标签
    existing_tags_set = set(existing_tags)
    for tag in request.tags:
        existing_tags_set.discard(tag)
    
    # 更新标签
    profile.tags = {"tags": list(existing_tags_set)}
    await repo.update_profile(profile)
    await session.commit()
    
    # 刷新数据
    await session.refresh(user)
    await session.refresh(profile)
    
    # 转换为DTO
    profile_dto = UserProfileDTO.from_user(user, profile)
    
    return success_response(
        data=profile_dto,
        message=f"成功删除 {len(request.tags)} 个标签",
    )
