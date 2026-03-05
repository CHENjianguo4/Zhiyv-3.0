"""
Sensitive Word Model

Defines the database model for sensitive words used in content moderation.
"""
from sqlalchemy import Column, BigInteger, String, Enum, TIMESTAMP, Index
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class SensitiveWordLevel(str, enum.Enum):
    """Sensitivity level of the word"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SensitiveWordAction(str, enum.Enum):
    """Action to take when word is detected"""
    REPLACE = "replace"  # Replace with ***
    BLOCK = "block"      # Block content submission
    REVIEW = "review"    # Send to manual review


class SensitiveWord(Base):
    """Sensitive word model for content filtering"""
    __tablename__ = "sensitive_words"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False, unique=True)
    level = Column(Enum(SensitiveWordLevel), nullable=False, default=SensitiveWordLevel.MEDIUM)
    category = Column(String(50))
    action = Column(Enum(SensitiveWordAction), nullable=False, default=SensitiveWordAction.BLOCK)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        Index('idx_level', 'level'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "word": self.word,
            "level": self.level.value if self.level else None,
            "category": self.category,
            "action": self.action.value if self.action else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
