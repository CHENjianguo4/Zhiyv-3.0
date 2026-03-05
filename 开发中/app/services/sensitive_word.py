"""
Sensitive Word Service

Business logic for sensitive word management with Redis caching.
"""
import json
from typing import List, Optional, Set
from redis.asyncio import Redis

from app.models.sensitive_word import SensitiveWord, SensitiveWordLevel, SensitiveWordAction
from app.repositories.sensitive_word import SensitiveWordRepository
from app.core.exceptions import ValidationError, NotFoundError


class SensitiveWordService:
    """Service for sensitive word management"""
    
    CACHE_KEY_ALL = "sensitive_words:all"
    CACHE_KEY_PREFIX = "sensitive_words:"
    CACHE_TTL = 3600  # 1 hour

    def __init__(self, repository: SensitiveWordRepository, redis: Redis):
        self.repository = repository
        self.redis = redis

    async def create_word(
        self,
        word: str,
        level: SensitiveWordLevel,
        category: Optional[str] = None,
        action: SensitiveWordAction = SensitiveWordAction.BLOCK
    ) -> SensitiveWord:
        """Create a new sensitive word"""
        # Check if word already exists
        existing = await self.repository.get_by_word(word)
        if existing:
            raise ValidationError(f"敏感词 '{word}' 已存在")
        
        # Create word
        sensitive_word = await self.repository.create(
            word=word,
            level=level,
            category=category,
            action=action
        )
        
        # Clear cache
        await self._clear_cache()
        
        return sensitive_word

    async def get_word(self, word_id: int) -> SensitiveWord:
        """Get sensitive word by ID"""
        sensitive_word = await self.repository.get_by_id(word_id)
        if not sensitive_word:
            raise NotFoundError(f"敏感词 ID {word_id} 不存在")
        return sensitive_word

    async def get_all_words(
        self,
        level: Optional[SensitiveWordLevel] = None,
        category: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[SensitiveWord]:
        """Get all sensitive words with optional filters"""
        return await self.repository.get_all(
            level=level,
            category=category,
            limit=limit,
            offset=offset
        )

    async def update_word(
        self,
        word_id: int,
        level: Optional[SensitiveWordLevel] = None,
        category: Optional[str] = None,
        action: Optional[SensitiveWordAction] = None
    ) -> SensitiveWord:
        """Update sensitive word"""
        sensitive_word = await self.repository.update(
            word_id=word_id,
            level=level,
            category=category,
            action=action
        )
        
        if not sensitive_word:
            raise NotFoundError(f"敏感词 ID {word_id} 不存在")
        
        # Clear cache
        await self._clear_cache()
        
        return sensitive_word

    async def delete_word(self, word_id: int) -> bool:
        """Delete sensitive word"""
        # Check if exists
        await self.get_word(word_id)
        
        # Delete
        deleted = await self.repository.delete(word_id)
        
        # Clear cache
        await self._clear_cache()
        
        return deleted

    async def bulk_import(self, words_data: List[dict]) -> dict:
        """Bulk import sensitive words"""
        success_count = 0
        failed_count = 0
        errors = []
        
        for data in words_data:
            try:
                # Validate required fields
                if "word" not in data or "level" not in data:
                    failed_count += 1
                    errors.append(f"缺少必填字段: {data}")
                    continue
                
                # Check if exists
                existing = await self.repository.get_by_word(data["word"])
                if existing:
                    failed_count += 1
                    errors.append(f"敏感词已存在: {data['word']}")
                    continue
                
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"导入失败: {data.get('word', 'unknown')} - {str(e)}")
        
        # Bulk create successful ones
        valid_data = [
            data for data in words_data
            if "word" in data and "level" in data
        ]
        
        if valid_data:
            await self.repository.bulk_create(valid_data)
        
        # Clear cache
        await self._clear_cache()
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors[:10]  # Return first 10 errors
        }

    async def get_word_set_from_cache(self) -> Set[str]:
        """Get all sensitive words as a set from cache"""
        # Try to get from cache
        cached = await self.redis.get(self.CACHE_KEY_ALL)
        
        if cached:
            word_list = json.loads(cached)
            return set(word_list)
        
        # If not in cache, load from database
        words = await self.repository.get_all(limit=10000)
        word_list = [w.word for w in words]
        word_set = set(word_list)
        
        # Cache for 1 hour
        await self.redis.setex(
            self.CACHE_KEY_ALL,
            self.CACHE_TTL,
            json.dumps(word_list)
        )
        
        return word_set

    async def check_content(self, content: str) -> dict:
        """Check if content contains sensitive words"""
        word_set = await self.get_word_set_from_cache()
        
        found_words = []
        for word in word_set:
            if word in content:
                found_words.append(word)
        
        return {
            "has_sensitive_words": len(found_words) > 0,
            "found_words": found_words,
            "count": len(found_words)
        }

    async def _clear_cache(self):
        """Clear all sensitive word caches"""
        await self.redis.delete(self.CACHE_KEY_ALL)

    async def get_statistics(self) -> dict:
        """Get sensitive word statistics"""
        total = await self.repository.count()
        
        # Count by level
        high_words = await self.repository.get_all(level=SensitiveWordLevel.HIGH)
        medium_words = await self.repository.get_all(level=SensitiveWordLevel.MEDIUM)
        low_words = await self.repository.get_all(level=SensitiveWordLevel.LOW)
        
        return {
            "total": total,
            "by_level": {
                "high": len(high_words),
                "medium": len(medium_words),
                "low": len(low_words)
            }
        }
