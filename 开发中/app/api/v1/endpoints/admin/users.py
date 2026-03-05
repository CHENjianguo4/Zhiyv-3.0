"""后台用户管理API

提供管理员对用户的管理功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.dependencies import get_db, get_current_user
from app.models.user import User, UserRole, UserStatus
from app.core.response import success_response, error_response
from app.schemas.user import UserProfileDTO

router = APIRouter()

def check_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/users", response_model=dict)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    keyword: Optional[str] = None,
    current_user: User = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表"""
    offset = (page - 1) * page_size
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)
    if keyword:
        query = query.where(User.nickname.contains(keyword) | User.student_id.contains(keyword))
        
    # 计算总数
    # total_query = select(func.count()).select_from(query.subquery())
    # total = await db.scalar(total_query)
    
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return success_response(
        data={
            "items": [UserProfileDTO.from_orm(u) for u in users],
            "total": 0 # 暂未实现总数查询
        }
    )


@router.put("/users/{user_id}/status", response_model=dict)
async def update_user_status(
    user_id: int,
    status: UserStatus,
    current_user: User = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新用户状态（封禁/解封）"""
    query = update(User).where(User.id == user_id).values(status=status)
    await db.execute(query)
    await db.commit()
    return success_response(message="用户状态更新成功")


@router.put("/users/{user_id}/role", response_model=dict)
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(check_admin),
    db: AsyncSession = Depends(get_db),
):
    """分配用户角色"""
    query = update(User).where(User.id == user_id).values(role=role)
    await db.execute(query)
    await db.commit()
    return success_response(message="用户角色更新成功")
