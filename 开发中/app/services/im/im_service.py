"""IM服务层

提供即时通讯业务逻辑，包括WebSocket连接管理、消息路由等
"""

import json
import asyncio
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket
from redis.asyncio import Redis

from app.core.logging import get_logger
from app.repositories.im.im_repo import ConversationRepository, MessageRepository
from app.models.im.conversation import Conversation, ConversationMember
from app.models.im.message import Message
from app.schemas.im import WSMessage

logger = get_logger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self, redis: Redis):
        # 本地连接池: user_id -> {websocket}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.redis = redis
        # 订阅Redis频道以处理分布式消息
        self.pubsub = self.redis.pubsub()

    async def connect(self, websocket: WebSocket, user_id: int):
        """建立连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        # 更新在线状态
        await self.redis.set(f"user:online:{user_id}", "1", ex=300)
        logger.info(f"User {user_id} connected")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: WSMessage, user_id: int):
        """发送个人消息（支持分布式）"""
        # 如果用户连接在当前实例
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message.model_dump())
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
        
        # 无论是否在本地，都通过Redis发布消息，确保多实例同步（简化版，实际应区分）
        # 这里为了简单，假设所有消息都通过Redis广播
        await self.redis.publish("im:channel", json.dumps({
            "target_user_id": user_id,
            "message": message.model_dump()
        }))

    async def broadcast(self, message: WSMessage):
        """广播消息"""
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                await connection.send_json(message.model_dump())


class IMService:
    """IM业务服务"""

    def __init__(
        self,
        conv_repo: ConversationRepository,
        msg_repo: MessageRepository,
        conn_manager: ConnectionManager
    ):
        self.conv_repo = conv_repo
        self.msg_repo = msg_repo
        self.manager = conn_manager

    async def handle_send_message(self, sender_id: int, data: dict):
        """处理发送消息"""
        conversation_id = data.get("conversation_id")
        content = data.get("content")
        msg_type = data.get("type", "text")
        
        # 1. 存储消息
        msg_doc = {
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "type": msg_type,
            "content": content,
            "created_at": datetime.utcnow(),
            "is_recalled": False,
            "read_by": [sender_id]
        }
        msg_id = await self.msg_repo.create_message(msg_doc)
        
        # 2. 更新会话状态
        conv = await self.conv_repo.get_conversation(conversation_id)
        if conv:
            conv.last_message_content = content if msg_type == "text" else f"[{msg_type}]"
            conv.last_message_time = datetime.utcnow()
            await self.conv_repo.update_conversation(conv)
        
        # 3. 实时推送
        # 获取会话成员（简化：假设是私聊，这里需要扩展群聊逻辑）
        member = await self.conv_repo.get_member(conversation_id, sender_id) # 这里的逻辑需要根据会话类型获取所有成员
        # TODO: 实际应获取所有成员ID并逐一推送
        
        ws_msg = WSMessage(
            action="new_msg",
            data={
                "id": msg_id,
                "conversation_id": conversation_id,
                "sender_id": sender_id,
                "content": content,
                "type": msg_type,
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        # 模拟推送给对方（实际需要查询成员表）
        # await self.manager.send_personal_message(ws_msg, target_user_id)
