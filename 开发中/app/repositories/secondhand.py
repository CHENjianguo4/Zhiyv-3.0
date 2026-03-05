"""二手商品仓储层

提供二手商品和订单相关的数据访问操作
"""

from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.secondhand import (
    ItemStatus,
    OrderStatus,
    SecondhandItem,
    SecondhandOrder,
)


class SecondhandItemRepository:
    """二手商品仓储类

    提供二手商品的CRUD操作和查询方法
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    # ==================== CRUD操作 ====================

    async def create(self, item: SecondhandItem) -> SecondhandItem:
        """创建商品

        Args:
            item: 商品对象

        Returns:
            SecondhandItem: 创建后的商品对象（包含ID）
        """
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: int) -> Optional[SecondhandItem]:
        """根据ID获取商品

        Args:
            item_id: 商品ID

        Returns:
            Optional[SecondhandItem]: 商品对象，不存在则返回None
        """
        query = select(SecondhandItem).where(
            SecondhandItem.id == item_id,
            SecondhandItem.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, item: SecondhandItem) -> SecondhandItem:
        """更新商品

        Args:
            item: 商品对象

        Returns:
            SecondhandItem: 更新后的商品对象
        """
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete(self, item: SecondhandItem) -> None:
        """删除商品（软删除）

        Args:
            item: 商品对象
        """
        from datetime import datetime

        item.deleted_at = datetime.utcnow()
        item.status = ItemStatus.REMOVED
        await self.session.flush()

    # ==================== 查询方法 ====================

    async def list_by_seller(
        self,
        seller_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SecondhandItem]:
        """根据卖家ID获取商品列表

        Args:
            seller_id: 卖家ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[SecondhandItem]: 商品列表
        """
        query = (
            select(SecondhandItem)
            .where(
                SecondhandItem.seller_id == seller_id,
                SecondhandItem.deleted_at.is_(None),
            )
            .order_by(SecondhandItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_status(
        self,
        school_id: int,
        status: ItemStatus,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SecondhandItem]:
        """根据状态获取商品列表

        Args:
            school_id: 学校ID
            status: 商品状态
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[SecondhandItem]: 商品列表
        """
        query = (
            select(SecondhandItem)
            .where(
                SecondhandItem.school_id == school_id,
                SecondhandItem.status == status,
                SecondhandItem.deleted_at.is_(None),
            )
            .order_by(SecondhandItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        school_id: int,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SecondhandItem]:
        """搜索商品

        Args:
            school_id: 学校ID
            keyword: 关键词（搜索标题和描述）
            category: 商品分类
            min_price: 最低价格
            max_price: 最高价格
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[SecondhandItem]: 商品列表
        """
        conditions = [
            SecondhandItem.school_id == school_id,
            SecondhandItem.status == ItemStatus.ON_SALE,
            SecondhandItem.deleted_at.is_(None),
        ]

        # 关键词搜索
        if keyword:
            conditions.append(
                or_(
                    SecondhandItem.title.contains(keyword),
                    SecondhandItem.description.contains(keyword),
                )
            )

        # 分类筛选
        if category:
            conditions.append(SecondhandItem.category == category)

        # 价格范围筛选
        if min_price is not None:
            conditions.append(SecondhandItem.selling_price >= min_price)
        if max_price is not None:
            conditions.append(SecondhandItem.selling_price <= max_price)

        query = (
            select(SecondhandItem)
            .where(and_(*conditions))
            .order_by(SecondhandItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_seller(self, seller_id: int) -> int:
        """统计卖家的商品数量

        Args:
            seller_id: 卖家ID

        Returns:
            int: 商品数量
        """
        from sqlalchemy import func

        query = select(func.count(SecondhandItem.id)).where(
            SecondhandItem.seller_id == seller_id,
            SecondhandItem.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def increment_view_count(self, item_id: int) -> None:
        """增加商品浏览次数

        Args:
            item_id: 商品ID
        """
        item = await self.get_by_id(item_id)
        if item:
            item.view_count += 1
            await self.session.flush()

    async def increment_favorite_count(self, item_id: int) -> None:
        """增加商品收藏次数

        Args:
            item_id: 商品ID
        """
        item = await self.get_by_id(item_id)
        if item:
            item.favorite_count += 1
            await self.session.flush()

    async def decrement_favorite_count(self, item_id: int) -> None:
        """减少商品收藏次数

        Args:
            item_id: 商品ID
        """
        item = await self.get_by_id(item_id)
        if item and item.favorite_count > 0:
            item.favorite_count -= 1
            await self.session.flush()


class SecondhandOrderRepository:
    """二手订单仓储类

    提供二手订单的CRUD操作和查询方法
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    # ==================== CRUD操作 ====================

    async def create(self, order: SecondhandOrder) -> SecondhandOrder:
        """创建订单

        Args:
            order: 订单对象

        Returns:
            SecondhandOrder: 创建后的订单对象（包含ID）
        """
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def get_by_id(self, order_id: int) -> Optional[SecondhandOrder]:
        """根据ID获取订单

        Args:
            order_id: 订单ID

        Returns:
            Optional[SecondhandOrder]: 订单对象，不存在则返回None
        """
        query = select(SecondhandOrder).where(SecondhandOrder.id == order_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, order: SecondhandOrder) -> SecondhandOrder:
        """更新订单

        Args:
            order: 订单对象

        Returns:
            SecondhandOrder: 更新后的订单对象
        """
        await self.session.flush()
        await self.session.refresh(order)
        return order

    # ==================== 查询方法 ====================

    async def list_by_buyer(
        self,
        buyer_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SecondhandOrder]:
        """根据买家ID获取订单列表

        Args:
            buyer_id: 买家ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[SecondhandOrder]: 订单列表
        """
        query = (
            select(SecondhandOrder)
            .where(SecondhandOrder.buyer_id == buyer_id)
            .order_by(SecondhandOrder.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_seller(
        self,
        seller_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[SecondhandOrder]:
        """根据卖家ID获取订单列表

        Args:
            seller_id: 卖家ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[SecondhandOrder]: 订单列表
        """
        query = (
            select(SecondhandOrder)
            .where(SecondhandOrder.seller_id == seller_id)
            .order_by(SecondhandOrder.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        order_id: int,
        status: OrderStatus,
    ) -> Optional[SecondhandOrder]:
        """更新订单状态

        Args:
            order_id: 订单ID
            status: 新状态

        Returns:
            Optional[SecondhandOrder]: 更新后的订单对象，不存在则返回None
        """
        order = await self.get_by_id(order_id)
        if order:
            order.status = status
            if status == OrderStatus.COMPLETED:
                from datetime import datetime

                order.completed_at = datetime.utcnow()
            await self.update(order)
        return order

    async def get_by_item_and_buyer(
        self,
        item_id: int,
        buyer_id: int,
    ) -> Optional[SecondhandOrder]:
        """根据商品ID和买家ID获取订单

        Args:
            item_id: 商品ID
            buyer_id: 买家ID

        Returns:
            Optional[SecondhandOrder]: 订单对象，不存在则返回None
        """
        query = select(SecondhandOrder).where(
            SecondhandOrder.item_id == item_id,
            SecondhandOrder.buyer_id == buyer_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_by_buyer(self, buyer_id: int) -> int:
        """统计买家的订单数量

        Args:
            buyer_id: 买家ID

        Returns:
            int: 订单数量
        """
        from sqlalchemy import func

        query = select(func.count(SecondhandOrder.id)).where(
            SecondhandOrder.buyer_id == buyer_id
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def count_by_seller(self, seller_id: int) -> int:
        """统计卖家的订单数量

        Args:
            seller_id: 卖家ID

        Returns:
            int: 订单数量
        """
        from sqlalchemy import func

        query = select(func.count(SecondhandOrder.id)).where(
            SecondhandOrder.seller_id == seller_id
        )
        result = await self.session.execute(query)
        return result.scalar_one()



class ItemFavoriteRepository:
    """商品收藏仓储类

    提供商品收藏的CRUD操作和查询方法
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    # ==================== CRUD操作 ====================

    async def create(self, user_id: int, item_id: int, school_id: int):
        """创建收藏

        Args:
            user_id: 用户ID
            item_id: 商品ID
            school_id: 学校ID

        Returns:
            ItemFavorite: 创建后的收藏对象
        """
        from app.models.secondhand import ItemFavorite

        favorite = ItemFavorite(
            user_id=user_id,
            item_id=item_id,
            school_id=school_id,
        )
        self.session.add(favorite)
        await self.session.flush()
        await self.session.refresh(favorite)
        return favorite

    async def delete(self, user_id: int, item_id: int) -> bool:
        """删除收藏

        Args:
            user_id: 用户ID
            item_id: 商品ID

        Returns:
            bool: 是否删除成功
        """
        from app.models.secondhand import ItemFavorite

        query = select(ItemFavorite).where(
            ItemFavorite.user_id == user_id,
            ItemFavorite.item_id == item_id,
        )
        result = await self.session.execute(query)
        favorite = result.scalar_one_or_none()

        if favorite:
            await self.session.delete(favorite)
            await self.session.flush()
            return True
        return False

    async def exists(self, user_id: int, item_id: int) -> bool:
        """检查收藏是否存在

        Args:
            user_id: 用户ID
            item_id: 商品ID

        Returns:
            bool: 是否已收藏
        """
        from app.models.secondhand import ItemFavorite

        query = select(ItemFavorite).where(
            ItemFavorite.user_id == user_id,
            ItemFavorite.item_id == item_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def list_by_user(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list:
        """获取用户的收藏列表

        Args:
            user_id: 用户ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[ItemFavorite]: 收藏列表
        """
        from app.models.secondhand import ItemFavorite

        query = (
            select(ItemFavorite)
            .where(ItemFavorite.user_id == user_id)
            .order_by(ItemFavorite.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        """统计用户的收藏数量

        Args:
            user_id: 用户ID

        Returns:
            int: 收藏数量
        """
        from sqlalchemy import func
        from app.models.secondhand import ItemFavorite

        query = select(func.count(ItemFavorite.id)).where(
            ItemFavorite.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def count_by_item(self, item_id: int) -> int:
        """统计商品的收藏数量

        Args:
            item_id: 商品ID

        Returns:
            int: 收藏数量
        """
        from sqlalchemy import func
        from app.models.secondhand import ItemFavorite

        query = select(func.count(ItemFavorite.id)).where(
            ItemFavorite.item_id == item_id
        )
        result = await self.session.execute(query)
        return result.scalar_one()


class PriceAlertRepository:
    """降价提醒仓储类

    提供降价提醒的CRUD操作和查询方法
    """

    def __init__(self, session: AsyncSession):
        """初始化仓储

        Args:
            session: 数据库会话
        """
        self.session = session

    # ==================== CRUD操作 ====================

    async def create(
        self,
        user_id: int,
        item_id: int,
        school_id: int,
        target_price: float,
    ):
        """创建降价提醒

        Args:
            user_id: 用户ID
            item_id: 商品ID
            school_id: 学校ID
            target_price: 目标价格

        Returns:
            PriceAlert: 创建后的提醒对象
        """
        from app.models.secondhand import PriceAlert
        from decimal import Decimal

        alert = PriceAlert(
            user_id=user_id,
            item_id=item_id,
            school_id=school_id,
            target_price=Decimal(str(target_price)),
            is_active=True,
        )
        self.session.add(alert)
        await self.session.flush()
        await self.session.refresh(alert)
        return alert

    async def get_by_user_and_item(
        self,
        user_id: int,
        item_id: int,
    ) -> Optional:
        """根据用户和商品获取提醒

        Args:
            user_id: 用户ID
            item_id: 商品ID

        Returns:
            Optional[PriceAlert]: 提醒对象，不存在则返回None
        """
        from app.models.secondhand import PriceAlert

        query = select(PriceAlert).where(
            PriceAlert.user_id == user_id,
            PriceAlert.item_id == item_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, alert) -> None:
        """更新提醒

        Args:
            alert: 提醒对象
        """
        await self.session.flush()
        await self.session.refresh(alert)

    async def delete(self, user_id: int, item_id: int) -> bool:
        """删除提醒

        Args:
            user_id: 用户ID
            item_id: 商品ID

        Returns:
            bool: 是否删除成功
        """
        from app.models.secondhand import PriceAlert

        query = select(PriceAlert).where(
            PriceAlert.user_id == user_id,
            PriceAlert.item_id == item_id,
        )
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()

        if alert:
            await self.session.delete(alert)
            await self.session.flush()
            return True
        return False

    async def list_by_user(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list:
        """获取用户的提醒列表

        Args:
            user_id: 用户ID
            offset: 偏移量
            limit: 限制数量

        Returns:
            list[PriceAlert]: 提醒列表
        """
        from app.models.secondhand import PriceAlert

        query = (
            select(PriceAlert)
            .where(PriceAlert.user_id == user_id)
            .order_by(PriceAlert.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_active_by_item(self, item_id: int) -> list:
        """获取商品的活跃提醒列表

        Args:
            item_id: 商品ID

        Returns:
            list[PriceAlert]: 提醒列表
        """
        from app.models.secondhand import PriceAlert

        query = select(PriceAlert).where(
            PriceAlert.item_id == item_id,
            PriceAlert.is_active == True,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        """统计用户的提醒数量

        Args:
            user_id: 用户ID

        Returns:
            int: 提醒数量
        """
        from sqlalchemy import func
        from app.models.secondhand import PriceAlert

        query = select(func.count(PriceAlert.id)).where(
            PriceAlert.user_id == user_id
        )
        result = await self.session.execute(query)
        return result.scalar_one()
