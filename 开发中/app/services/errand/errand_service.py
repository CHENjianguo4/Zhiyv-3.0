"""跑腿服务逻辑层

提供跑腿订单的业务逻辑处理
"""

import random
import string
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.core.logging import get_logger
from app.repositories.errand.errand_repo import ErrandRepository
from app.models.errand.order import ErrandOrder, ErrandStatus
from app.core.exceptions import ValidationError, ResourceNotFoundError, PermissionDeniedError

logger = get_logger(__name__)


class ErrandService:
    """跑腿服务类"""

    def __init__(self, repo: ErrandRepository):
        self.repo = repo

    async def create_order(
        self,
        publisher_id: int,
        school_id: int,
        title: str,
        description: str,
        price: Decimal,
        delivery_location: str,
        pickup_location: Optional[str] = None,
        deadline: Optional[datetime] = None,
        is_public: bool = True
    ) -> ErrandOrder:
        """创建跑腿订单"""
        # 生成6位数字验证码
        verification_code = "".join(random.choices(string.digits, k=6))
        
        order = ErrandOrder(
            publisher_id=publisher_id,
            school_id=school_id,
            title=title,
            description=description,
            price=price,
            delivery_location=delivery_location,
            pickup_location=pickup_location,
            deadline=deadline,
            is_public=is_public,
            verification_code=verification_code,
            status=ErrandStatus.PENDING
        )
        
        created_order = await self.repo.create(order)
        logger.info(f"Errand order created: {created_order.id} by user {publisher_id}")
        return created_order

    async def accept_order(self, order_id: int, runner_id: int) -> ErrandOrder:
        """接单"""
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found")
            
        if order.status != ErrandStatus.PENDING:
            raise ValidationError("Order is not available")
            
        if order.publisher_id == runner_id:
            raise PermissionDeniedError("Cannot accept own order")
            
        order.runner_id = runner_id
        order.status = ErrandStatus.ACCEPTED
        order.accepted_at = datetime.utcnow()
        
        updated_order = await self.repo.update(order)
        logger.info(f"Order {order_id} accepted by user {runner_id}")
        return updated_order

    async def complete_order(self, order_id: int, code: str, user_id: int) -> ErrandOrder:
        """完成订单（验证码校验）"""
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found")
            
        if order.runner_id != user_id:
            raise PermissionDeniedError("Only runner can complete order")
            
        if order.verification_code != code:
            raise ValidationError("Invalid verification code")
            
        order.status = ErrandStatus.COMPLETED
        order.completed_at = datetime.utcnow()
        
        updated_order = await self.repo.update(order)
        logger.info(f"Order {order_id} completed")
        return updated_order

    async def list_available_orders(
        self,
        school_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[ErrandOrder]:
        """获取可接订单"""
        offset = (page - 1) * page_size
        return await self.repo.list_available(school_id, offset, page_size)
