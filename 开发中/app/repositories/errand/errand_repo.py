"""跑腿服务仓储层

提供跑腿订单相关的数据访问操作
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.errand.order import ErrandOrder, ErrandStatus


class ErrandRepository:
    """跑腿订单仓储类"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, order: ErrandOrder) -> ErrandOrder:
        """创建订单"""
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def get_by_id(self, order_id: int) -> Optional[ErrandOrder]:
        """获取订单详情"""
        query = select(ErrandOrder).where(ErrandOrder.id == order_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_available(
        self,
        school_id: int,
        offset: int = 0,
        limit: int = 20
    ) -> List[ErrandOrder]:
        """获取可接订单列表"""
        query = select(ErrandOrder).where(
            ErrandOrder.school_id == school_id,
            ErrandOrder.status == ErrandStatus.PENDING,
            ErrandOrder.is_public == True
        ).order_by(ErrandOrder.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_publisher(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20
    ) -> List[ErrandOrder]:
        """获取用户发布的订单"""
        query = select(ErrandOrder).where(
            ErrandOrder.publisher_id == user_id
        ).order_by(ErrandOrder.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_runner(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20
    ) -> List[ErrandOrder]:
        """获取用户接单的订单"""
        query = select(ErrandOrder).where(
            ErrandOrder.runner_id == user_id
        ).order_by(ErrandOrder.accepted_at.desc()).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, order: ErrandOrder) -> ErrandOrder:
        """更新订单"""
        await self.session.flush()
        await self.session.refresh(order)
        return order
