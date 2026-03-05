"""
Tests for Sensitive Word Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.sensitive_word import SensitiveWordService
from app.models.sensitive_word import SensitiveWord, SensitiveWordLevel, SensitiveWordAction
from app.core.exceptions import ValidationError, NotFoundError


@pytest.fixture
def mock_repository():
    """Mock sensitive word repository"""
    return AsyncMock()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def service(mock_repository, mock_redis):
    """Create service instance with mocked dependencies"""
    return SensitiveWordService(mock_repository, mock_redis)


@pytest.mark.asyncio
async def test_create_word_success(service, mock_repository):
    """Test creating a new sensitive word"""
    # Arrange
    mock_repository.get_by_word.return_value = None
    mock_word = SensitiveWord(
        id=1,
        word="测试敏感词",
        level=SensitiveWordLevel.HIGH,
        action=SensitiveWordAction.BLOCK
    )
    mock_repository.create.return_value = mock_word
    
    # Act
    result = await service.create_word(
        word="测试敏感词",
        level=SensitiveWordLevel.HIGH,
        action=SensitiveWordAction.BLOCK
    )
    
    # Assert
    assert result.word == "测试敏感词"
    assert result.level == SensitiveWordLevel.HIGH
    mock_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_word_duplicate(service, mock_repository):
    """Test creating a duplicate sensitive word raises error"""
    # Arrange
    existing_word = SensitiveWord(
        id=1,
        word="重复词",
        level=SensitiveWordLevel.MEDIUM,
        action=SensitiveWordAction.BLOCK
    )
    mock_repository.get_by_word.return_value = existing_word
    
    # Act & Assert
    with pytest.raises(ValidationError, match="已存在"):
        await service.create_word(
            word="重复词",
            level=SensitiveWordLevel.HIGH,
            action=SensitiveWordAction.BLOCK
        )


@pytest.mark.asyncio
async def test_get_word_success(service, mock_repository):
    """Test getting a sensitive word by ID"""
    # Arrange
    mock_word = SensitiveWord(
        id=1,
        word="测试词",
        level=SensitiveWordLevel.LOW,
        action=SensitiveWordAction.REPLACE
    )
    mock_repository.get_by_id.return_value = mock_word
    
    # Act
    result = await service.get_word(1)
    
    # Assert
    assert result.id == 1
    assert result.word == "测试词"


@pytest.mark.asyncio
async def test_get_word_not_found(service, mock_repository):
    """Test getting non-existent word raises error"""
    # Arrange
    mock_repository.get_by_id.return_value = None
    
    # Act & Assert
    with pytest.raises(NotFoundError, match="不存在"):
        await service.get_word(999)


@pytest.mark.asyncio
async def test_check_content_with_sensitive_words(service, mock_repository, mock_redis):
    """Test checking content that contains sensitive words"""
    # Arrange
    import json
    mock_redis.get.return_value = json.dumps(["敏感词1", "敏感词2", "违规"])
    
    # Act
    result = await service.check_content("这是一段包含敏感词1的内容")
    
    # Assert
    assert result["has_sensitive_words"] is True
    assert "敏感词1" in result["found_words"]
    assert result["count"] == 1


@pytest.mark.asyncio
async def test_check_content_without_sensitive_words(service, mock_repository, mock_redis):
    """Test checking clean content"""
    # Arrange
    import json
    mock_redis.get.return_value = json.dumps(["敏感词1", "敏感词2"])
    
    # Act
    result = await service.check_content("这是一段正常的内容")
    
    # Assert
    assert result["has_sensitive_words"] is False
    assert len(result["found_words"]) == 0
    assert result["count"] == 0


@pytest.mark.asyncio
async def test_bulk_import_success(service, mock_repository):
    """Test bulk importing sensitive words"""
    # Arrange
    mock_repository.get_by_word.return_value = None
    mock_repository.bulk_create.return_value = None
    
    words_data = [
        {"word": "词1", "level": SensitiveWordLevel.HIGH, "action": SensitiveWordAction.BLOCK},
        {"word": "词2", "level": SensitiveWordLevel.MEDIUM, "action": SensitiveWordAction.REVIEW}
    ]
    
    # Act
    result = await service.bulk_import(words_data)
    
    # Assert
    assert result["success_count"] == 2
    assert result["failed_count"] == 0
    mock_repository.bulk_create.assert_called_once()


@pytest.mark.asyncio
async def test_delete_word_success(service, mock_repository):
    """Test deleting a sensitive word"""
    # Arrange
    mock_word = SensitiveWord(
        id=1,
        word="待删除",
        level=SensitiveWordLevel.LOW,
        action=SensitiveWordAction.REPLACE
    )
    mock_repository.get_by_id.return_value = mock_word
    mock_repository.delete.return_value = True
    
    # Act
    result = await service.delete_word(1)
    
    # Assert
    assert result is True
    mock_repository.delete.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_statistics(service, mock_repository):
    """Test getting sensitive word statistics"""
    # Arrange
    mock_repository.count.return_value = 100
    mock_repository.get_all.side_effect = [
        [MagicMock()] * 30,  # high
        [MagicMock()] * 50,  # medium
        [MagicMock()] * 20,  # low
    ]
    
    # Act
    result = await service.get_statistics()
    
    # Assert
    assert result["total"] == 100
    assert result["by_level"]["high"] == 30
    assert result["by_level"]["medium"] == 50
    assert result["by_level"]["low"] == 20
