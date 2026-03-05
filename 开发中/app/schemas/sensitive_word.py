"""
Sensitive Word Schemas

Pydantic models for sensitive word API requests and responses.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.sensitive_word import SensitiveWordLevel, SensitiveWordAction


class SensitiveWordCreate(BaseModel):
    """Schema for creating a sensitive word"""
    word: str = Field(..., min_length=1, max_length=100, description="敏感词")
    level: SensitiveWordLevel = Field(..., description="敏感级别")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    action: SensitiveWordAction = Field(
        default=SensitiveWordAction.BLOCK,
        description="处理动作"
    )


class SensitiveWordUpdate(BaseModel):
    """Schema for updating a sensitive word"""
    level: Optional[SensitiveWordLevel] = Field(None, description="敏感级别")
    category: Optional[str] = Field(None, max_length=50, description="分类")
    action: Optional[SensitiveWordAction] = Field(None, description="处理动作")


class SensitiveWordResponse(BaseModel):
    """Schema for sensitive word response"""
    id: int
    word: str
    level: SensitiveWordLevel
    category: Optional[str]
    action: SensitiveWordAction
    created_at: datetime

    class Config:
        from_attributes = True


class SensitiveWordBulkImport(BaseModel):
    """Schema for bulk importing sensitive words"""
    words: List[SensitiveWordCreate] = Field(..., description="敏感词列表")


class SensitiveWordBulkImportResponse(BaseModel):
    """Schema for bulk import response"""
    success_count: int = Field(..., description="成功导入数量")
    failed_count: int = Field(..., description="失败数量")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class SensitiveWordCheckRequest(BaseModel):
    """Schema for checking content"""
    content: str = Field(..., min_length=1, description="待检测内容")


class SensitiveWordCheckResponse(BaseModel):
    """Schema for content check response"""
    has_sensitive_words: bool = Field(..., description="是否包含敏感词")
    found_words: List[str] = Field(default_factory=list, description="发现的敏感词")
    count: int = Field(..., description="敏感词数量")


class SensitiveWordStatistics(BaseModel):
    """Schema for sensitive word statistics"""
    total: int = Field(..., description="总数")
    by_level: dict = Field(..., description="按级别统计")
