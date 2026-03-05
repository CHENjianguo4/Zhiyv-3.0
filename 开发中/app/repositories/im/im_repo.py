"""IM仓储层

提供IM相关的数据访问操作
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.im.conversation import Conversation, ConversationMember
from app.models.im.message import Message


class ConversationRepository:
    """会话仓储类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """创建会话"""
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """获取会话详情"""
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_user_conversations(
        self, user_id: int, offset: int = 0, limit: int = 20
    ) -> List[Conversation]:
        """获取用户会话列表"""
        # 连接查询：Member -> Conversation
        query = (
            select(Conversation, ConversationMember)
            .join(ConversationMember, Conversation.id == ConversationMember.conversation_id)
            .where(ConversationMember.user_id == user_id)
            .order_by(ConversationMember.is_top.desc(), Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        # 组装返回结果，注入member属性
        conversations = []
        for conv, member in result:
            conv.unread_count = member.unread_count
            conv.is_muted = member.is_muted
            conv.is_top = member.is_top
            conversations.append(conv)
        return conversations

    async def add_member(self, member: ConversationMember) -> ConversationMember:
        """添加成员"""
        self.session.add(member)
        return member

    async def get_member(self, conversation_id: int, user_id: int) -> Optional[ConversationMember]:
        """获取成员信息"""
        query = select(ConversationMember).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """更新会话信息"""
        self.session.add(conversation)
        return conversation


class MessageRepository:
    """消息仓储类（MongoDB）"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["messages"]

    async def create_message(self, message: dict) -> str:
        """创建消息"""
        result = await self.collection.insert_one(message)
        return str(result.inserted_id)

    async def list_messages(
        self, conversation_id: int, before_time: Optional[datetime] = None, limit: int = 20
    ) -> List[dict]:
        """获取历史消息"""
        query = {"conversation_id": conversation_id}
        if before_time:
            query["created_at"] = {"$lt": before_time}
        
        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        # 转换 ObjectId 为 str
        for msg in messages:
            msg["id"] = str(msg["_id"])
            del msg["_id"]
        return messages[::-1]  # 按时间正序返回

    async def recall_message(self, message_id: str):
        """撤回消息"""
        await self.collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"is_recalled": True, "updated_at": datetime.utcnow()}}
        )
