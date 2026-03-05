"""
Tests for Content Audit Service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.content_audit import ContentAuditEngine, DFAFilter, ContentAuditResult


@pytest.fixture
def mock_sensitive_word_service():
    """Mock sensitive word service"""
    service = AsyncMock()
    service.get_word_set_from_cache = AsyncMock(
        return_value={"敏感词1", "敏感词2", "违规内容"}
    )
    return service


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    return AsyncMock()


@pytest.fixture
def audit_engine(mock_sensitive_word_service, mock_redis):
    """Create audit engine instance"""
    return ContentAuditEngine(mock_sensitive_word_service, mock_redis)


@pytest.mark.asyncio
async def test_audit_text_clean_content(audit_engine):
    """Test auditing clean content"""
    result = await audit_engine.audit_text("这是一段正常的内容")
    
    assert result.passed is True
    assert result.action == "approve"
    assert len(result.found_words) == 0


@pytest.mark.asyncio
async def test_audit_text_with_sensitive_words(audit_engine):
    """Test auditing content with sensitive words"""
    result = await audit_engine.audit_text("这段内容包含敏感词1")
    
    assert result.passed is False
    assert result.action in ["block", "review"]
    assert "敏感词1" in result.found_words


@pytest.mark.asyncio
async def test_audit_text_strict_mode(audit_engine):
    """Test strict mode blocks any sensitive word"""
    result = await audit_engine.audit_text(
        "这段内容包含敏感词1",
        strict_mode=True
    )
    
    assert result.passed is False
    assert result.action == "block"


@pytest.mark.asyncio
async def test_audit_text_multiple_sensitive_words(audit_engine):
    """Test content with multiple sensitive words"""
    result = await audit_engine.audit_text(
        "这段内容包含敏感词1和敏感词2还有违规内容"
    )
    
    assert result.passed is False
    assert result.action == "block"
    assert len(result.found_words) >= 3


@pytest.mark.asyncio
async def test_audit_empty_content(audit_engine):
    """Test auditing empty content"""
    result = await audit_engine.audit_text("")
    
    assert result.passed is True
    assert result.action == "approve"


@pytest.mark.asyncio
async def test_audit_mixed_content(audit_engine):
    """Test auditing mixed content (text + images)"""
    result = await audit_engine.audit_content(
        text="正常内容",
        images=["http://example.com/image.jpg"]
    )
    
    assert result.passed is True
    assert result.action == "approve"


def test_dfa_filter_add_word():
    """Test adding words to DFA filter"""
    dfa = DFAFilter()
    dfa.add_word("测试")
    dfa.add_word("敏感词")
    
    assert dfa.word_count == 2


def test_dfa_filter_search():
    """Test searching for sensitive words"""
    dfa = DFAFilter()
    dfa.build_from_words(["敏感词", "违规"])
    
    matches = dfa.search("这是敏感词和违规内容")
    
    assert len(matches) == 2
    assert matches[0][0] == "敏感词"
    assert matches[1][0] == "违规"


def test_dfa_filter_text():
    """Test filtering text"""
    dfa = DFAFilter()
    dfa.build_from_words(["敏感词", "违规"])
    
    filtered = dfa.filter_text("这是敏感词和违规内容", "*")
    
    assert "敏感词" not in filtered
    assert "违规" not in filtered
    assert "***" in filtered


def test_dfa_filter_empty_text():
    """Test filtering empty text"""
    dfa = DFAFilter()
    dfa.build_from_words(["敏感词"])
    
    filtered = dfa.filter_text("", "*")
    
    assert filtered == ""


def test_dfa_filter_no_matches():
    """Test filtering text with no matches"""
    dfa = DFAFilter()
    dfa.build_from_words(["敏感词"])
    
    text = "这是正常内容"
    filtered = dfa.filter_text(text, "*")
    
    assert filtered == text
