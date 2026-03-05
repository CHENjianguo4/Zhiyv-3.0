"""二手商品模型单元测试"""

from decimal import Decimal

import pytest

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


class TestSecondhandItem:
    """测试SecondhandItem模型"""

    def test_create_item(self):
        """测试创建商品"""
        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="二手iPhone 13",
            description="9成新，无划痕",
            category=ItemCategory.ELECTRONICS,
            condition=ItemCondition.LIKE_NEW,
            original_price=Decimal("5999.00"),
            selling_price=Decimal("3999.00"),
            location="东校区宿舍楼",
            is_negotiable=True,
            delivery_method=DeliveryMethod.BOTH,
            status=ItemStatus.ON_SALE,
        )

        assert item.seller_id == 1
        assert item.school_id == 1
        assert item.title == "二手iPhone 13"
        assert item.category == ItemCategory.ELECTRONICS
        assert item.condition == ItemCondition.LIKE_NEW
        assert item.selling_price == Decimal("3999.00")
        assert item.is_negotiable is True
        assert item.status == ItemStatus.ON_SALE

    def test_item_default_values(self):
        """测试商品默认值"""
        item = SecondhandItem(
            seller_id=1,
            school_id=1,
            title="测试商品",
            category=ItemCategory.OTHER,
            condition=ItemCondition.WELL_USED,
            selling_price=Decimal("100.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
        )

        assert item.view_count == 0
        assert item.favorite_count == 0
        assert item.status == ItemStatus.DRAFT
        assert item.is_negotiable is False

    def test_item_repr(self):
        """测试商品字符串表示"""
        item = SecondhandItem(
            id=123,
            seller_id=1,
            school_id=1,
            title="测试商品",
            category=ItemCategory.TEXTBOOK,
            condition=ItemCondition.BRAND_NEW,
            selling_price=Decimal("50.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
            status=ItemStatus.ON_SALE,
        )

        repr_str = repr(item)
        assert "SecondhandItem" in repr_str
        assert "id=123" in repr_str
        assert "title=测试商品" in repr_str
        assert "price=50.00" in repr_str


class TestSecondhandOrder:
    """测试SecondhandOrder模型"""

    def test_create_order(self):
        """测试创建订单"""
        order = SecondhandOrder(
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("3999.00"),
            delivery_method=DeliveryMethod.EXPRESS,
            delivery_address="北京市海淀区某某大学",
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID,
            escrow_amount=Decimal("3999.00"),
            buyer_note="请尽快发货",
        )

        assert order.item_id == 1
        assert order.buyer_id == 2
        assert order.seller_id == 1
        assert order.school_id == 1
        assert order.price == Decimal("3999.00")
        assert order.delivery_method == DeliveryMethod.EXPRESS
        assert order.status == OrderStatus.PENDING
        assert order.payment_status == PaymentStatus.UNPAID
        assert order.escrow_amount == Decimal("3999.00")

    def test_order_default_values(self):
        """测试订单默认值"""
        order = SecondhandOrder(
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("100.00"),
            delivery_method=DeliveryMethod.FACE_TO_FACE,
        )

        assert order.status == OrderStatus.PENDING
        assert order.payment_status == PaymentStatus.UNPAID
        assert order.completed_at is None

    def test_order_repr(self):
        """测试订单字符串表示"""
        order = SecondhandOrder(
            id=456,
            item_id=1,
            buyer_id=2,
            seller_id=1,
            school_id=1,
            price=Decimal("3999.00"),
            delivery_method=DeliveryMethod.EXPRESS,
            status=OrderStatus.CONFIRMED,
        )

        repr_str = repr(order)
        assert "SecondhandOrder" in repr_str
        assert "id=456" in repr_str
        assert "item_id=1" in repr_str
        assert "buyer_id=2" in repr_str
        assert "seller_id=1" in repr_str
        assert "price=3999.00" in repr_str


class TestEnums:
    """测试枚举类型"""

    def test_item_category_enum(self):
        """测试商品分类枚举"""
        assert ItemCategory.ELECTRONICS.value == "electronics"
        assert ItemCategory.TEXTBOOK.value == "textbook"
        assert ItemCategory.DAILY.value == "daily"
        assert ItemCategory.SPORTS.value == "sports"
        assert ItemCategory.OTHER.value == "other"

    def test_item_condition_enum(self):
        """测试商品成色枚举"""
        assert ItemCondition.BRAND_NEW.value == "brand_new"
        assert ItemCondition.LIKE_NEW.value == "like_new"
        assert ItemCondition.LIGHTLY_USED.value == "lightly_used"
        assert ItemCondition.WELL_USED.value == "well_used"
        assert ItemCondition.HEAVILY_USED.value == "heavily_used"

    def test_item_status_enum(self):
        """测试商品状态枚举"""
        assert ItemStatus.DRAFT.value == "draft"
        assert ItemStatus.ON_SALE.value == "on_sale"
        assert ItemStatus.SOLD.value == "sold"
        assert ItemStatus.REMOVED.value == "removed"
        assert ItemStatus.BANNED.value == "banned"

    def test_delivery_method_enum(self):
        """测试交易方式枚举"""
        assert DeliveryMethod.FACE_TO_FACE.value == "face_to_face"
        assert DeliveryMethod.EXPRESS.value == "express"
        assert DeliveryMethod.BOTH.value == "both"

    def test_order_status_enum(self):
        """测试订单状态枚举"""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.CONFIRMED.value == "confirmed"
        assert OrderStatus.DELIVERING.value == "delivering"
        assert OrderStatus.COMPLETED.value == "completed"
        assert OrderStatus.CANCELLED.value == "cancelled"
        assert OrderStatus.DISPUTED.value == "disputed"

    def test_payment_status_enum(self):
        """测试支付状态枚举"""
        assert PaymentStatus.UNPAID.value == "unpaid"
        assert PaymentStatus.PAID.value == "paid"
        assert PaymentStatus.REFUNDED.value == "refunded"
