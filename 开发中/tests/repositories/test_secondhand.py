"""二手商品仓储层单元测试"""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.secondhand import (
    DeliveryMethod,
    ItemCategory,
    ItemCondition,
    ItemStatus,
    OrderStatus,
    PaymentStatus,
    SecondhandItem,
    SecondhandOrder,
)
from app.repositories.secondhand import (
    SecondhandItemRepository,
    SecondhandOrderRepository,
)


@pytest.mark.asyncio
class TestSecondhandItemRepository:
    """测试SecondhandItemRepository"""

    async def test_create_item(self, db_session: AsyncSession):
        """测试创建商品"""
        repo = SecondhandItemRepository(db_session)

        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="测试商品",
            category=ItemCategory.ELECTRONICS,
            condition=ItemCondition.LIKE_NEW,
            selling_price=Decimal("999.00"),
            delivery_method=DeliveryMethod.BOTH,
        )

        created_item = await repo.create(item)

        assert created_item.id is not None
        assert created_item.title == "测试商品"
        assert created_item.seller_id == 1

    async def test_get_by_id(self, db_session: AsyncSession):
        """测试根据ID获取商品"""
        repo = SecondhandItemRepository(db_session)

        # 创建商品
        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="测试商品",
            category=ItemCategory.TEXTBOOK,
            condition=ItemCondition.BRAND_NEW,
            selling_price=Decimal("50.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
        )
        created_item = await repo.create(item)
        await db_session.commit()

        # 获取商品
        found_item = await repo.get_by_id(created_item.id)

        assert found_item is not None
        assert found_item.id == created_item.id
        assert found_item.title == "测试商品"

    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """测试获取不存在的商品"""
        repo = SecondhandItemRepository(db_session)

        found_item = await repo.get_by_id(99999)

        assert found_item is None

    async def test_update_item(self, db_session: AsyncSession):
        """测试更新商品"""
        repo = SecondhandItemRepository(db_session)

        # 创建商品
        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="原标题",
            category=ItemCategory.DAILY,
            condition=ItemCondition.WELL_USED,
            selling_price=Decimal("100.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
        )
        created_item = await repo.create(item)
        await db_session.commit()

        # 更新商品
        created_item.title = "新标题"
        created_item.selling_price = Decimal("80.00")
        updated_item = await repo.update(created_item)
        await db_session.commit()

        # 验证更新
        found_item = await repo.get_by_id(updated_item.id)
        assert found_item.title == "新标题"
        assert found_item.selling_price == Decimal("80.00")

    async def test_delete_item(self, db_session: AsyncSession):
        """测试删除商品（软删除）"""
        repo = SecondhandItemRepository(db_session)

        # 创建商品
        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="待删除商品",
            category=ItemCategory.OTHER,
            condition=ItemCondition.LIGHTLY_USED,
            selling_price=Decimal("50.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
        )
        created_item = await repo.create(item)
        await db_session.commit()

        # 删除商品
        await repo.delete(created_item)
        await db_session.commit()

        # 验证软删除
        found_item = await repo.get_by_id(created_item.id)
        assert found_item is None  # 软删除后查询不到

    async def test_list_by_seller(self, db_session: AsyncSession):
        """测试根据卖家ID获取商品列表"""
        repo = SecondhandItemRepository(db_session)

        # 创建多个商品
        for i in range(3):
            item = SecondhandItem(
                seller_id=1,
                school_id=1,
                title=f"商品{i}",
                category=ItemCategory.ELECTRONICS,
                condition=ItemCondition.LIKE_NEW,
                selling_price=Decimal("100.00"),
                delivery_method=DeliveryMethod.BOTH,
            )
            await repo.create(item)
        await db_session.commit()

        # 获取列表
        items = await repo.list_by_seller(seller_id=1, limit=10)

        assert len(items) >= 3
        assert all(item.seller_id == 1 for item in items)

    async def test_list_by_status(self, db_session: AsyncSession):
        """测试根据状态获取商品列表"""
        repo = SecondhandItemRepository(db_session)

        # 创建在售商品
        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="在售商品",
            category=ItemCategory.SPORTS,
            condition=ItemCondition.BRAND_NEW,
            selling_price=Decimal("200.00"),
            delivery_method=DeliveryMethod.EXPRESS,
            status=ItemStatus.ON_SALE,
        )
        await repo.create(item)
        await db_session.commit()

        # 获取在售商品列表
        items = await repo.list_by_status(
            school_id=1, status=ItemStatus.ON_SALE, limit=10
        )

        assert len(items) >= 1
        assert all(item.status == ItemStatus.ON_SALE for item in items)

    async def test_search(self, db_session: AsyncSession):
        """测试搜索商品"""
        repo = SecondhandItemRepository(db_session)

        # 创建测试商品
        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="iPhone 13 Pro",
            description="全新未拆封",
            category=ItemCategory.ELECTRONICS,
            condition=ItemCondition.BRAND_NEW,
            selling_price=Decimal("6999.00"),
            delivery_method=DeliveryMethod.BOTH,
            status=ItemStatus.ON_SALE,
        )
        await repo.create(item)
        await db_session.commit()

        # 搜索商品
        items = await repo.search(
            school_id=1,
            keyword="iPhone",
            category=ItemCategory.ELECTRONICS.value,
            min_price=5000.0,
            max_price=8000.0,
        )

        assert len(items) >= 1
        assert any("iPhone" in item.title for item in items)

    async def test_increment_view_count(self, db_session: AsyncSession):
        """测试增加浏览次数"""
        repo = SecondhandItemRepository(db_session)

        # 创建商品
        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="测试商品",
            category=ItemCategory.DAILY,
            condition=ItemCondition.WELL_USED,
            selling_price=Decimal("50.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
        )
        created_item = await repo.create(item)
        await db_session.commit()

        initial_count = created_item.view_count

        # 增加浏览次数
        await repo.increment_view_count(created_item.id)
        await db_session.commit()

        # 验证
        found_item = await repo.get_by_id(created_item.id)
        assert found_item.view_count == initial_count + 1


@pytest.mark.asyncio
class TestSecondhandOrderRepository:
    """测试SecondhandOrderRepository"""

    async def test_create_order(self, db_session: AsyncSession):
        """测试创建订单"""
        repo = SecondhandOrderRepository(db_session)

        order = SecondhandOrder(
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("999.00"),
            delivery_method=DeliveryMethod.EXPRESS,
        )

        created_order = await repo.create(order)

        assert created_order.id is not None
        assert created_order.item_id == 1
        assert created_order.buyer_id == 2
        assert created_order.seller_id == 1

    async def test_get_by_id(self, db_session: AsyncSession):
        """测试根据ID获取订单"""
        repo = SecondhandOrderRepository(db_session)

        # 创建订单
        order = SecondhandOrder(
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("500.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
        )
        created_order = await repo.create(order)
        await db_session.commit()

        # 获取订单
        found_order = await repo.get_by_id(created_order.id)

        assert found_order is not None
        assert found_order.id == created_order.id
        assert found_order.price == Decimal("500.00")

    async def test_list_by_buyer(self, db_session: AsyncSession):
        """测试根据买家ID获取订单列表"""
        repo = SecondhandOrderRepository(db_session)

        # 创建订单
        order = SecondhandOrder(
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("300.00"),
            delivery_method=DeliveryMethod.EXPRESS,
        )
        await repo.create(order)
        await db_session.commit()

        # 获取列表
        orders = await repo.list_by_buyer(buyer_id=2, limit=10)

        assert len(orders) >= 1
        assert all(order.buyer_id == 2 for order in orders)

    async def test_list_by_seller(self, db_session: AsyncSession):
        """测试根据卖家ID获取订单列表"""
        repo = SecondhandOrderRepository(db_session)

        # 创建订单
        order = SecondhandOrder(
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("400.00"),
            delivery_method=DeliveryMethod.BOTH,
        )
        await repo.create(order)
        await db_session.commit()

        # 获取列表
        orders = await repo.list_by_seller(seller_id=1, limit=10)

        assert len(orders) >= 1
        assert all(order.seller_id == 1 for order in orders)

    async def test_update_status(self, db_session: AsyncSession):
        """测试更新订单状态"""
        repo = SecondhandOrderRepository(db_session)

        # 创建订单
        order = SecondhandOrder(
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("600.00"),
            delivery_method=DeliveryMethod.EXPRESS,
            status=OrderStatus.PENDING,
        )
        created_order = await repo.create(order)
        await db_session.commit()

        # 更新状态
        updated_order = await repo.update_status(
            created_order.id, OrderStatus.CONFIRMED
        )
        await db_session.commit()

        assert updated_order is not None
        assert updated_order.status == OrderStatus.CONFIRMED

    async def test_update_status_to_completed(self, db_session: AsyncSession):
        """测试更新订单状态为已完成"""
        repo = SecondhandOrderRepository(db_session)

        # 创建订单
        order = SecondhandOrder(
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("700.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
            status=OrderStatus.CONFIRMED,
        )
        created_order = await repo.create(order)
        await db_session.commit()

        # 更新为已完成
        updated_order = await repo.update_status(
            created_order.id, OrderStatus.COMPLETED
        )
        await db_session.commit()

        assert updated_order is not None
        assert updated_order.status == OrderStatus.COMPLETED
        assert updated_order.completed_at is not None
