"""
Content Audit API Endpoints

Handles content moderation and filtering.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.dependencies import get_db_session, get_redis
from app.core.response import success_response
from app.repositories.sensitive_word import SensitiveWordRepository
from app.services.sensitive_word import SensitiveWordService
from app.services.content_audit import ContentAuditEngine, DFAFilter
from app.schemas.audit import (
    ContentAuditRequest,
    ContentAuditResponse,
    BatchAuditRequest,
    BatchAuditResponse,
    TextFilterRequest,
    TextFilterResponse
)

router = APIRouter(prefix="/audit", tags=["audit"])


async def get_audit_engine(
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis)
) -> ContentAuditEngine:
    """Get content audit engine instance"""
    repository = SensitiveWordRepository(db)
    sensitive_word_service = SensitiveWordService(repository, redis)
    return ContentAuditEngine(sensitive_word_service, redis)


@router.post("/content", response_model=ContentAuditResponse)
async def audit_content(
    request: ContentAuditRequest,
    engine: ContentAuditEngine = Depends(get_audit_engine)
):
    """
    审核内容（文本和/或图片）
    
    支持文本和图片的混合审核，返回审核结果和处理建议。
    """
    result = await engine.audit_content(
        text=request.text,
        images=request.images,
        strict_mode=request.strict_mode
    )
    return success_response(data=result.to_dict())


@router.post("/text", response_model=ContentAuditResponse)
async def audit_text(
    text: str,
    strict_mode: bool = False,
    engine: ContentAuditEngine = Depends(get_audit_engine)
):
    """
    审核文本内容
    
    快速检测文本中的敏感词。
    """
    result = await engine.audit_text(text, strict_mode)
    return success_response(data=result.to_dict())


@router.post("/batch", response_model=BatchAuditResponse)
async def batch_audit(
    request: BatchAuditRequest,
    engine: ContentAuditEngine = Depends(get_audit_engine)
):
    """
    批量审核内容
    
    一次性审核多个内容，提高效率。
    """
    contents = [
        {
            "text": item.text,
            "images": item.images,
            "strict_mode": item.strict_mode
        }
        for item in request.contents
    ]
    
    results = await engine.batch_audit(contents)
    
    # Calculate statistics
    passed_count = sum(1 for r in results if r.action == "approve")
    blocked_count = sum(1 for r in results if r.action == "block")
    review_count = sum(1 for r in results if r.action == "review")
    
    return success_response(data={
        "results": [r.to_dict() for r in results],
        "total": len(results),
        "passed_count": passed_count,
        "blocked_count": blocked_count,
        "review_count": review_count
    })


@router.post("/filter", response_model=TextFilterResponse)
async def filter_text(
    request: TextFilterRequest,
    db: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis)
):
    """
    过滤文本中的敏感词
    
    将敏感词替换为指定字符（默认为 *）。
    使用 DFA 算法实现高效过滤。
    """
    # Get sensitive words
    repository = SensitiveWordRepository(db)
    sensitive_word_service = SensitiveWordService(repository, redis)
    word_set = await sensitive_word_service.get_word_set_from_cache()
    
    # Build DFA filter
    dfa = DFAFilter()
    dfa.build_from_words(list(word_set))
    
    # Filter text
    filtered_text = dfa.filter_text(request.text, request.replace_char)
    
    # Find what was replaced
    matches = dfa.search(request.text)
    found_words = list(set([match[0] for match in matches]))
    
    return success_response(data={
        "original_text": request.text,
        "filtered_text": filtered_text,
        "found_words": found_words,
        "replaced_count": len(matches)
    })
