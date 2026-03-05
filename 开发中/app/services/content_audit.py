"""
Content Audit Service

Implements content moderation engine with sensitive word detection
and external AI audit integration.
"""
import re
from typing import Dict, List, Optional, Set
from redis.asyncio import Redis

from app.services.sensitive_word import SensitiveWordService
from app.models.sensitive_word import SensitiveWordAction


class ContentAuditResult:
    """Content audit result"""
    
    def __init__(
        self,
        passed: bool,
        action: str,
        reason: Optional[str] = None,
        found_words: Optional[List[str]] = None,
        confidence: float = 1.0
    ):
        self.passed = passed
        self.action = action  # "approve", "block", "review"
        self.reason = reason
        self.found_words = found_words or []
        self.confidence = confidence
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "action": self.action,
            "reason": self.reason,
            "found_words": self.found_words,
            "confidence": self.confidence
        }


class ContentAuditEngine:
    """Content audit engine with multiple detection strategies"""
    
    def __init__(
        self,
        sensitive_word_service: SensitiveWordService,
        redis: Redis
    ):
        self.sensitive_word_service = sensitive_word_service
        self.redis = redis
        self._word_set: Optional[Set[str]] = None
    
    async def _load_sensitive_words(self) -> Set[str]:
        """Load sensitive words from cache or database"""
        if self._word_set is None:
            self._word_set = await self.sensitive_word_service.get_word_set_from_cache()
        return self._word_set
    
    async def audit_text(
        self,
        content: str,
        strict_mode: bool = False
    ) -> ContentAuditResult:
        """
        Audit text content for sensitive words
        
        Args:
            content: Text content to audit
            strict_mode: If True, block on any sensitive word found
        
        Returns:
            ContentAuditResult with audit decision
        """
        if not content or not content.strip():
            return ContentAuditResult(
                passed=True,
                action="approve",
                reason="Empty content"
            )
        
        # Check sensitive words
        word_set = await self._load_sensitive_words()
        found_words = self._detect_sensitive_words(content, word_set)
        
        if not found_words:
            return ContentAuditResult(
                passed=True,
                action="approve"
            )
        
        # Determine action based on found words
        if strict_mode or len(found_words) >= 3:
            return ContentAuditResult(
                passed=False,
                action="block",
                reason=f"检测到 {len(found_words)} 个敏感词",
                found_words=found_words
            )
        elif len(found_words) >= 1:
            return ContentAuditResult(
                passed=False,
                action="review",
                reason=f"检测到 {len(found_words)} 个敏感词，需要人工审核",
                found_words=found_words
            )
        
        return ContentAuditResult(
            passed=True,
            action="approve"
        )

    def _detect_sensitive_words(
        self,
        content: str,
        word_set: Set[str]
    ) -> List[str]:
        """
        Detect sensitive words in content using simple matching
        
        Args:
            content: Content to check
            word_set: Set of sensitive words
        
        Returns:
            List of found sensitive words
        """
        found = []
        content_lower = content.lower()
        
        for word in word_set:
            if word.lower() in content_lower:
                found.append(word)
        
        return found
    
    async def audit_image(
        self,
        image_url: str
    ) -> ContentAuditResult:
        """
        Audit image content (placeholder for external API integration)
        
        In production, this would integrate with Tencent Cloud Content Security API
        or similar services for image moderation.
        
        Args:
            image_url: URL of the image to audit
        
        Returns:
            ContentAuditResult with audit decision
        """
        # TODO: Integrate with Tencent Cloud Content Security API
        # For now, return approve
        return ContentAuditResult(
            passed=True,
            action="approve",
            reason="Image audit not implemented yet"
        )
    
    async def audit_content(
        self,
        text: Optional[str] = None,
        images: Optional[List[str]] = None,
        strict_mode: bool = False
    ) -> ContentAuditResult:
        """
        Audit mixed content (text + images)
        
        Args:
            text: Text content
            images: List of image URLs
            strict_mode: Strict audit mode
        
        Returns:
            Combined audit result
        """
        results = []
        
        # Audit text
        if text:
            text_result = await self.audit_text(text, strict_mode)
            results.append(text_result)
        
        # Audit images
        if images:
            for image_url in images:
                image_result = await self.audit_image(image_url)
                results.append(image_result)
        
        # Combine results - fail if any check fails
        if not results:
            return ContentAuditResult(
                passed=True,
                action="approve",
                reason="No content to audit"
            )
        
        # If any result is blocked, block the content
        for result in results:
            if result.action == "block":
                return result
        
        # If any result needs review, send to review
        for result in results:
            if result.action == "review":
                return result
        
        # All passed
        return ContentAuditResult(
            passed=True,
            action="approve"
        )
    
    async def batch_audit(
        self,
        contents: List[Dict[str, any]]
    ) -> List[ContentAuditResult]:
        """
        Batch audit multiple contents
        
        Args:
            contents: List of content dicts with 'text' and/or 'images'
        
        Returns:
            List of audit results
        """
        results = []
        for content in contents:
            result = await self.audit_content(
                text=content.get("text"),
                images=content.get("images"),
                strict_mode=content.get("strict_mode", False)
            )
            results.append(result)
        return results


class DFAFilter:
    """
    DFA (Deterministic Finite Automaton) algorithm for efficient
    sensitive word detection.
    
    This is more efficient than simple string matching for large word sets.
    """
    
    def __init__(self):
        self.root = {}
        self.word_count = 0
    
    def add_word(self, word: str):
        """Add a word to the DFA tree"""
        if not word:
            return
        
        node = self.root
        for char in word:
            if char not in node:
                node[char] = {}
            node = node[char]
        
        node['is_end'] = True
        self.word_count += 1
    
    def build_from_words(self, words: List[str]):
        """Build DFA tree from word list"""
        for word in words:
            self.add_word(word)
    
    def search(self, text: str) -> List[tuple]:
        """
        Search for sensitive words in text
        
        Returns:
            List of (word, start_pos, end_pos) tuples
        """
        found = []
        text_len = len(text)
        
        i = 0
        while i < text_len:
            node = self.root
            j = i
            matched_word = ""
            
            while j < text_len and text[j] in node:
                matched_word += text[j]
                node = node[text[j]]
                
                if node.get('is_end'):
                    found.append((matched_word, i, j + 1))
                
                j += 1
            
            i += 1
        
        return found
    
    def filter_text(self, text: str, replace_char: str = "*") -> str:
        """Replace sensitive words with replace_char"""
        matches = self.search(text)
        
        if not matches:
            return text
        
        # Sort by position (reverse to replace from end to start)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        result = list(text)
        for word, start, end in matches:
            for i in range(start, end):
                result[i] = replace_char
        
        return ''.join(result)
