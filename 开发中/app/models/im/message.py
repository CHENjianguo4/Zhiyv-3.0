"""IM消息模型

定义MongoDB中的消息文档结构
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """消息文档模型"""
    
    id: Optional[str] = Field(None, alias="_id")
    conversation_id: int = Field(..., description="会话ID")
    sender_id: int = Field(..., description="发送者ID")
    
    # 消息内容
    type: str = Field(default="text", description="类型(text/image/voice/location)")
    content: str = Field(..., description="消息内容(文本或URL)")
    extra: Dict[str, Any] = Field(default_factory=dict, description="扩展信息(时长、位置坐标等)")
    
    # 状态
    is_recalled: bool = Field(default=False, description="是否撤回")
    read_by: List[int] = Field(default_factory=list, description="已读用户列表")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow, description="发送时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
