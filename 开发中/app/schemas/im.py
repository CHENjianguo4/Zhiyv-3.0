"""IM相关Pydantic模式"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class ConversationResponse(BaseModel):
    """会话响应模式"""
    
    id: int
    type: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    last_message_content: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    is_muted: bool = False
    is_top: bool = False
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """消息创建请求模式"""
    
    conversation_id: int
    type: str = Field(default="text", description="类型(text/image/voice/location)")
    content: str = Field(..., min_length=1, description="内容")
    extra: Dict[str, Any] = Field(default_factory=dict, description="扩展信息")


class MessageResponse(BaseModel):
    """消息响应模式"""
    
    id: str
    conversation_id: int
    sender_id: int
    type: str
    content: str
    extra: Dict[str, Any]
    is_recalled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class WSMessage(BaseModel):
    """WebSocket消息统一格式"""
    
    action: str = Field(..., description="操作类型(send_msg/recall_msg/read_report/heartbeat)")
    data: Dict[str, Any] = Field(..., description="业务数据")
    request_id: Optional[str] = None
