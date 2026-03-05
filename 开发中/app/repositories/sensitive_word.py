"""
Sensitive Word Repository

Handles database operations for sensitive words.
"""
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensitive_word import SensitiveWord, SensitiveWordLevel, SensitiveWordAction


class SensitiveWordRepository:
    """Repository for sensitive word database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        word: str,
        level: SensitiveWordLevel,
        category: Optional[str] = None,
        action: SensitiveWordAction = SensitiveWordAction.BLOCK
    ) -> SensitiveWord:
        """Create a new sensitive word"""
        sensitive_word = SensitiveWord(
            word=word,
            level=level,
            category=category,
            action=action
        )
        self.db.add(sensitive_word)
        await self.db.commit()
        await self.db.refresh(sensitive_word)
        return sensitive_word

    async def get_by_id(self, word_id: int) -> Optional[SensitiveWord]:
        """Get sensitive word by ID"""
        result = await self.db.execute(
            select(SensitiveWord).where(SensitiveWord.id == word_id)
        )
        return result.scalar_one_or_none()

    async def get_by_word(self, word: str) -> Optional[SensitiveWord]:
        """Get sensitive word by word text"""
        result = await self.db.execute(
            select(SensitiveWord).where(SensitiveWord.word == word)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        level: Optional[SensitiveWordLevel] = None,
        category: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[SensitiveWord]:
        """Get all sensitive words with optional filters"""
        query = select(SensitiveWord)
        
        if level:
            query = query.where(SensitiveWord.level == level)
        if category:
            query = query.where(SensitiveWord.category == category)
        
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        word_id: int,
        level: Optional[SensitiveWordLevel] = None,
        category: Optional[str] = None,
        action: Optional[SensitiveWordAction] = None
    ) -> Optional[SensitiveWord]:
        """Update sensitive word"""
        sensitive_word = await self.get_by_id(word_id)
        if not sensitive_word:
            return None
        
        if level is not None:
            sensitive_word.level = level
        if category is not None:
            sensitive_word.category = category
        if action is not None:
            sensitive_word.action = action
        
        await self.db.commit()
        await self.db.refresh(sensitive_word)
        return sensitive_word

    async def delete(self, word_id: int) -> bool:
        """Delete sensitive word"""
        result = await self.db.execute(
            delete(SensitiveWord).where(SensitiveWord.id == word_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def bulk_create(self, words_data: List[dict]) -> int:
        """Bulk create sensitive words"""
        sensitive_words = [
            SensitiveWord(**data) for data in words_data
        ]
        self.db.add_all(sensitive_words)
        await self.db.commit()
        return len(sensitive_words)

    async def count(self) -> int:
        """Count total sensitive words"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).select_from(SensitiveWord)
        )
        return result.scalar_one()
