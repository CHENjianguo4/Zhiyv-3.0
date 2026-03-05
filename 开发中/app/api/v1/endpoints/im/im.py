"""IM相关API接口"""

from typing import List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, get_redis
from app.models.user import User
from app.services.im.im_service import IMService, ConnectionManager
from app.repositories.im.im_repo import ConversationRepository, MessageRepository
from app.schemas.im import ConversationResponse, MessageResponse
from app.core.response import success_response, error_response

router = APIRouter()

# 依赖注入
async def get_im_service(
    db: AsyncSession = Depends(get_db),
    # mongodb: AsyncIOMotorDatabase = Depends(get_mongodb), # 需要添加mongodb依赖
    # redis: Redis = Depends(get_redis)
) -> IMService:
    # 临时占位，需要完善依赖注入
    pass


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    # service: IMService = Depends(get_im_service)
):
    """WebSocket连接端点"""
    # 验证Token获取用户ID
    user_id = 1 # 临时
    
    # await service.manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            # await service.handle_ws_message(user_id, data)
    except WebSocketDisconnect:
        # service.manager.disconnect(websocket, user_id)
        pass


@router.get("/conversations", response_model=dict)
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
):
    """获取会话列表"""
    return success_response(data=[], message="获取会话列表成功")


@router.get("/conversations/{conversation_id}/messages", response_model=dict)
async def list_messages(
    conversation_id: int,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """获取历史消息"""
    return success_response(data=[], message="获取消息成功")
