"""内容解析与格式化工具

提供Markdown解析、URL识别、文本过滤等功能
"""

import re
import bleach
import markdown
from typing import List, Optional

class ContentFormatter:
    """内容格式化工具类"""

    @staticmethod
    def parse_markdown(text: str) -> str:
        """解析Markdown为HTML"""
        if not text:
            return ""
        
        # 允许的标签和属性
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img', 'span'
        ]
        allowed_attrs = {
            'a': ['href', 'title', 'target'],
            'img': ['src', 'alt', 'title'],
            '*': ['class']
        }
        
        # 转换Markdown
        html = markdown.markdown(
            text,
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        
        # 清洗HTML（防止XSS）
        clean_html = bleach.clean(
            html,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        )
        
        return clean_html

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """提取文本中的URL"""
        if not text:
            return []
            
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        return url_pattern.findall(text)

    @staticmethod
    def filter_html(text: str) -> str:
        """过滤HTML标签（仅保留纯文本）"""
        if not text:
            return ""
        return bleach.clean(text, tags=[], strip=True)

    @staticmethod
    def truncate_text(text: str, length: int = 100, suffix: str = "...") -> str:
        """截断文本"""
        if not text:
            return ""
        if len(text) <= length:
            return text
        return text[:length] + suffix
