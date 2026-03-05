"""数据管理API

提供数据导入导出接口
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, Response
from typing import Optional

from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.core.utils.export.transfer import DataTransfer
from app.core.response import success_response, error_response

router = APIRouter()

def check_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/export/users", response_class=Response)
async def export_users(
    current_user: User = Depends(check_admin),
):
    """导出用户数据"""
    # 模拟数据
    data = [
        {"id": 1, "nickname": "User1", "role": "user", "created_at": "2024-01-01"},
        {"id": 2, "nickname": "User2", "role": "admin", "created_at": "2024-01-02"},
    ]
    csv_content = DataTransfer.export_csv(["id", "nickname", "role", "created_at"], data)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )


@router.post("/import/courses", response_model=dict)
async def import_courses(
    file: UploadFile = File(...),
    current_user: User = Depends(check_admin),
):
    """导入课程数据"""
    content = (await file.read()).decode("utf-8")
    data = DataTransfer.import_csv(content)
    
    # TODO: 批量插入数据库
    
    return success_response(
        data={"count": len(data)},
        message=f"成功导入 {len(data)} 条数据"
    )
