"""
Sensitive Words API Endpoints

Handles CRUD operations for sensitive words management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.dependencies import get_db_session, get_redis, require_admin
from app.core.response import success_response
from app.repositories.sensitive_word import SensitiveWordRepository
from app.services.sensitive_word import SensitiveWordService
from app.schemas.sensitive_word import (
    SensitiveWordCreate,
    SensitiveWordUpdate,
    SensitiveWordResponse,
    SensitiveWordBulkImport,
    SensitiveWordBulkImportResponse,
    SensitiveWordCheckRequest,
    SensitiveWordCheckResponse,
    SensitiveWordStatistics
)
from app.models.sensitive_word import SensitiveWordLevel

router = APIRouter(prefix="/sensitive-words", tags=["sensitive-words"])


def get_service(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis)
) -> SensitiveWordService:
    """Get sensitive word service instance"""
    repository = SensitiveWordRepository(db)
    return SensitiveWordService(repository, redis)


@router.post("", response_model=SensitiveWordResponse, dependencies=[Depends(require_admin)])
async def create_sensitive_word(
    data: SensitiveWordCreate,
    service: SensitiveWordService = Depends(get_service)
):
    """
    创建敏感词
    
    需要管理员权限
    """
    word = await service.create_word(
        word=data.word,
        level=data.level,
        category=data.category,
        action=data.action
    )
    return success_response(data=word.to_dict())


@router.get("", response_model=List[SensitiveWordResponse], dependencies=[Depends(require_admin)])
async def get_sensitive_words(
    level: Optional[SensitiveWordLevel] = Query(None, description="敏感级别筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    service: SensitiveWordService = Depends(get_service)
):
    """
    获取敏感词列表
    
    需要管理员权限
    """
    words = await service.get_all_words(
        level=level,
        category=category,
        limit=limit,
        offset=offset
    )
    return success_response(data=[w.to_dict() for w in words])


@router.get("/{word_id}", response_model=SensitiveWordResponse, dependencies=[Depends(require_admin)])
async def get_sensitive_word(
    word_id: int,
    service: SensitiveWordService = Depends(get_service)
):
    """
    获取单个敏感词详情
    
    需要管理员权限
    """
    word = await service.get_word(word_id)
    return success_response(data=word.to_dict())


@router.put("/{word_id}", response_model=SensitiveWordResponse, dependencies=[Depends(require_admin)])
async def update_sensitive_word(
    word_id: int,
    data: SensitiveWordUpdate,
    service: SensitiveWordService = Depends(get_service)
):
    """
    更新敏感词
    
    需要管理员权限
    """
    word = await service.update_word(
        word_id=word_id,
        level=data.level,
        category=data.category,
        action=data.action
    )
    return success_response(data=word.to_dict())


@router.delete("/{word_id}", dependencies=[Depends(require_admin)])
async def delete_sensitive_word(
    word_id: int,
    service: SensitiveWordService = Depends(get_service)
):
    """
    删除敏感词
    
    需要管理员权限
    """
    await service.delete_word(word_id)
    return success_response(message="敏感词删除成功")


@router.post("/bulk-import", response_model=SensitiveWordBulkImportResponse, dependencies=[Depends(require_admin)])
async def bulk_import_sensitive_words(
    data: SensitiveWordBulkImport,
    service: SensitiveWordService = Depends(get_service)
):
    """
    批量导入敏感词
    
    需要管理员权限
    """
    words_data = [word.dict() for word in data.words]
    result = await service.bulk_import(words_data)
    return success_response(data=result)


@router.post("/check", response_model=SensitiveWordCheckResponse)
async def check_content(
    data: SensitiveWordCheckRequest,
    service: SensitiveWordService = Depends(get_service)
):
    """
    检测内容是否包含敏感词
    
    所有用户可用
    """
    result = await service.check_content(data.content)
    return success_response(data=result)


@router.get("/statistics/summary", response_model=SensitiveWordStatistics, dependencies=[Depends(require_admin)])
async def get_statistics(
    service: SensitiveWordService = Depends(get_service)
):
    """
    获取敏感词统计信息
    
    需要管理员权限
    """
    stats = await service.get_statistics()
    return success_response(data=stats)
