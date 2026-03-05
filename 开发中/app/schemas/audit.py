"""
Content Audit Schemas

Pydantic models for content audit API requests and responses.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ContentAuditRequest(BaseModel):
    """Schema for content audit request"""
    text: Optional[str] = Field(None, description="文本内容")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    strict_mode: bool = Field(default=False, description="严格模式")


class ContentAuditResponse(BaseModel):
    """Schema for content audit response"""
    passed: bool = Field(..., description="是否通过审核")
    action: str = Field(..., description="处理动作: approve/block/review")
    reason: Optional[str] = Field(None, description="原因")
    found_words: List[str] = Field(default_factory=list, description="发现的敏感词")
    confidence: float = Field(default=1.0, description="置信度")


class BatchAuditRequest(BaseModel):
    """Schema for batch audit request"""
    contents: List[ContentAuditRequest] = Field(..., description="待审核内容列表")


class BatchAuditResponse(BaseModel):
    """Schema for batch audit response"""
    results: List[ContentAuditResponse] = Field(..., description="审核结果列表")
    total: int = Field(..., description="总数")
    passed_count: int = Field(..., description="通过数量")
    blocked_count: int = Field(..., description="拦截数量")
    review_count: int = Field(..., description="待审核数量")


class TextFilterRequest(BaseModel):
    """Schema for text filter request"""
    text: str = Field(..., min_length=1, description="待过滤文本")
    replace_char: str = Field(default="*", max_length=1, description="替换字符")


class TextFilterResponse(BaseModel):
    """Schema for text filter response"""
    original_text: str = Field(..., description="原始文本")
    filtered_text: str = Field(..., description="过滤后文本")
    found_words: List[str] = Field(default_factory=list, description="发现的敏感词")
    replaced_count: int = Field(..., description="替换数量")
