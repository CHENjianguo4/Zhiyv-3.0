"""
Tests for SecondhandOrderService

Tests order creation, confirmation, completion, and cancellation.
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.services.secondhand import SecondhandOrderService
from app.models.secondhand import (
    SecondhandItem,
    SecondhandOrder,
    ItemStatus,
    ItemCategory,
    ItemCondition,
    DeliveryMethod,
    OrderStatus,
    PaymentStatus,
)
from app.core.exceptions import (
    ValidationError,
    PermissionDeniedError,
    ResourceNotFoundError,
)


@pytest.fixture
def mock_order_repo():
    """Mock order repository"""
    return AsyncMock()


@pytest.fixture
def mock_item_repo():
    """Mock item repository"""
    return AsyncMock()


@pytest.fixture
def order_service(mock_order_repo, mock_item_repo):
    """Create order service with mocked dependencies"""
    return SecondhandOrderService(
        order_repository=mock_order_repo,
        item_repository=mock_item_repo,
    )


@pytest.fixture
def sample_item():
    """Create a sample item"""
    item = MagicMock(spec=SecondhandItem)
    item.id = 1
    item.seller_id = 100
    item.school_id = 1
    item.title = "Test Item"
    item.selling_price = Decimal("50.00")
    item.status = ItemStatus.ON_SALE
    item.delivery_method = DeliveryMethod.FACE_TO_FACE
    return item


@pytest.fixture
def sample_order():
    """Create a sample order"""
    order = MagicMock(spec=SecondhandOrder)
    order.id = 1
    order.item_id = 1
    order.buyer_id = 200
    order.seller_id = 100
    order.school_id = 1
    order.price = Decimal("50.00")
    order.delivery_method = DeliveryMethod.FACE_TO_FACE
    order.status = OrderStatus.PENDING
    order.payment_status = PaymentStatus.UNPAID
    return order


# ==================== Create Order Tests ====================


@pytest.mark.asyncio
async def test_create_order_success(order_service, mock_item_repo, mock_order_repo, sample_item, sample_order):
    """Test successful order creation"""
    # Setup
    mock_item_repo.get_by_id.return_value = sample_item
    mock_order_repo.get_by_item_and_buyer.return_value = None
    mock_order_repo.create.return_value = sample_order
    
    # Execute
    order = await order_service.create_order(
        buyer_id=200,
        item_id=1,
        school_id=1,
        delivery_method="face_to_face",
    )
    
    # Assert
    assert order is not None
    mock_item_repo.get_by_id.assert_called_once_with(1)
    mock_order_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_item_not_found(order_service, mock_item_repo):
    """Test order creation fails when item not found"""
    # Setup
    mock_item_repo.get_by_id.return_value = None
    
    # Execute & Assert
    with pytest.raises(ResourceNotFoundError, match="Item 1 not found"):
        await order_service.create_order(
            buyer_id=200,
            item_id=1,
            school_id=1,
            delivery_method="face_to_face",
        )


@pytest.mark.asyncio
async def test_create_order_item_not_available(order_service, mock_item_repo, sample_item):
    """Test order creation fails when item is not available"""
    # Setup
    sample_item.status = ItemStatus.SOLD
    mock_item_repo.get_by_id.return_value = sample_item
    
    # Execute & Assert
    with pytest.raises(ValidationError, match="Item is not available for purchase"):
        await order_service.create_order(
            buyer_id=200,
            item_id=1,
            school_id=1,
            delivery_method="face_to_face",
        )


@pytest.mark.asyncio
async def test_create_order_buyer_is_seller(order_service, mock_item_repo, sample_item):
    """Test order creation fails when buyer is the seller"""
    # Setup
    mock_item_repo.get_by_id.return_value = sample_item
    
    # Execute & Assert
    with pytest.raises(PermissionDeniedError, match="You cannot buy your own item"):
        await order_service.create_order(
            buyer_id=100,  # Same as seller_id
            item_id=1,
            school_id=1,
            delivery_method="face_to_face",
        )


@pytest.mark.asyncio
async def test_create_order_invalid_delivery_method(order_service, mock_item_repo, sample_item):
    """Test order creation fails with invalid delivery method"""
    # Setup
    mock_item_repo.get_by_id.return_value = sample_item
    
    # Execute & Assert
    with pytest.raises(ValidationError, match="Invalid delivery method"):
        await order_service.create_order(
            buyer_id=200,
            item_id=1,
            school_id=1,
            delivery_method="invalid_method",
        )


@pytest.mark.asyncio
async def test_create_order_express_without_address(order_service, mock_item_repo, mock_order_repo, sample_item):
    """Test order creation fails when express delivery without address"""
    # Setup
    mock_item_repo.get_by_id.return_value = sample_item
    mock_order_repo.get_by_item_and_buyer.return_value = None
    
    # Execute & Assert
    with pytest.raises(ValidationError, match="Delivery address is required for express delivery"):
        await order_service.create_order(
            buyer_id=200,
            item_id=1,
            school_id=1,
            delivery_method="express",
            delivery_address=None,
        )


@pytest.mark.asyncio
async def test_create_order_duplicate_active_order(order_service, mock_item_repo, mock_order_repo, sample_item, sample_order):
    """Test order creation fails when active order already exists"""
    # Setup
    mock_item_repo.get_by_id.return_value = sample_item
    existing_order = sample_order
    existing_order.status = OrderStatus.PENDING
    mock_order_repo.get_by_item_and_buyer.return_value = existing_order
    
    # Execute & Assert
    with pytest.raises(ValidationError, match="You already have an active order for this item"):
        await order_service.create_order(
            buyer_id=200,
            item_id=1,
            school_id=1,
            delivery_method="face_to_face",
        )


# ==================== Get Order Tests ====================


@pytest.mark.asyncio
async def test_get_order_success_as_buyer(order_service, mock_order_repo, sample_order):
    """Test successful order retrieval as buyer"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute
    order = await order_service.get_order(order_id=1, user_id=200)
    
    # Assert
    assert order is not None
    mock_order_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_order_success_as_seller(order_service, mock_order_repo, sample_order):
    """Test successful order retrieval as seller"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute
    order = await order_service.get_order(order_id=1, user_id=100)
    
    # Assert
    assert order is not None


@pytest.mark.asyncio
async def test_get_order_not_found(order_service, mock_order_repo):
    """Test order retrieval fails when order not found"""
    # Setup
    mock_order_repo.get_by_id.return_value = None
    
    # Execute & Assert
    with pytest.raises(ResourceNotFoundError, match="Order 1 not found"):
        await order_service.get_order(order_id=1, user_id=200)


@pytest.mark.asyncio
async def test_get_order_permission_denied(order_service, mock_order_repo, sample_order):
    """Test order retrieval fails when user is not buyer or seller"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute & Assert
    with pytest.raises(PermissionDeniedError, match="You can only view your own orders"):
        await order_service.get_order(order_id=1, user_id=999)


# ==================== Confirm Order Tests ====================


@pytest.mark.asyncio
async def test_confirm_order_success(order_service, mock_order_repo, sample_order):
    """Test successful order confirmation by seller"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    mock_order_repo.update.return_value = sample_order
    
    # Execute
    order = await order_service.confirm_order(order_id=1, seller_id=100)
    
    # Assert
    assert order.status == OrderStatus.CONFIRMED
    mock_order_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_order_not_seller(order_service, mock_order_repo, sample_order):
    """Test order confirmation fails when user is not the seller"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute & Assert
    with pytest.raises(PermissionDeniedError, match="Only the seller can confirm the order"):
        await order_service.confirm_order(order_id=1, seller_id=999)


@pytest.mark.asyncio
async def test_confirm_order_invalid_status(order_service, mock_order_repo, sample_order):
    """Test order confirmation fails when order status is not pending"""
    # Setup
    sample_order.status = OrderStatus.COMPLETED
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute & Assert
    with pytest.raises(ValidationError, match="Cannot confirm order with status"):
        await order_service.confirm_order(order_id=1, seller_id=100)


# ==================== Complete Order Tests ====================


@pytest.mark.asyncio
async def test_complete_order_success(order_service, mock_order_repo, mock_item_repo, sample_order, sample_item):
    """Test successful order completion by buyer"""
    # Setup
    sample_order.status = OrderStatus.CONFIRMED
    mock_order_repo.get_by_id.return_value = sample_order
    mock_order_repo.update.return_value = sample_order
    mock_item_repo.get_by_id.return_value = sample_item
    mock_item_repo.update.return_value = sample_item
    
    # Execute
    order = await order_service.complete_order(order_id=1, buyer_id=200)
    
    # Assert
    assert order.status == OrderStatus.COMPLETED
    assert sample_item.status == ItemStatus.SOLD
    mock_order_repo.update.assert_called_once()
    mock_item_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_complete_order_not_buyer(order_service, mock_order_repo, sample_order):
    """Test order completion fails when user is not the buyer"""
    # Setup
    sample_order.status = OrderStatus.CONFIRMED
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute & Assert
    with pytest.raises(PermissionDeniedError, match="Only the buyer can complete the order"):
        await order_service.complete_order(order_id=1, buyer_id=999)


@pytest.mark.asyncio
async def test_complete_order_invalid_status(order_service, mock_order_repo, sample_order):
    """Test order completion fails when order status is not confirmed"""
    # Setup
    sample_order.status = OrderStatus.PENDING
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute & Assert
    with pytest.raises(ValidationError, match="Cannot complete order with status"):
        await order_service.complete_order(order_id=1, buyer_id=200)


# ==================== Cancel Order Tests ====================


@pytest.mark.asyncio
async def test_cancel_order_by_buyer(order_service, mock_order_repo, sample_order):
    """Test successful order cancellation by buyer"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    mock_order_repo.update.return_value = sample_order
    
    # Execute
    order = await order_service.cancel_order(
        order_id=1,
        user_id=200,
        cancel_reason="Changed my mind"
    )
    
    # Assert
    assert order.status == OrderStatus.CANCELLED
    mock_order_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_order_by_seller(order_service, mock_order_repo, sample_order):
    """Test successful order cancellation by seller"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    mock_order_repo.update.return_value = sample_order
    
    # Execute
    order = await order_service.cancel_order(
        order_id=1,
        user_id=100,
        cancel_reason="Item no longer available"
    )
    
    # Assert
    assert order.status == OrderStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_order_permission_denied(order_service, mock_order_repo, sample_order):
    """Test order cancellation fails when user is not buyer or seller"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute & Assert
    with pytest.raises(PermissionDeniedError, match="Only buyer or seller can cancel the order"):
        await order_service.cancel_order(order_id=1, user_id=999)


@pytest.mark.asyncio
async def test_cancel_order_already_completed(order_service, mock_order_repo, sample_order):
    """Test order cancellation fails when order is already completed"""
    # Setup
    sample_order.status = OrderStatus.COMPLETED
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute & Assert
    with pytest.raises(ValidationError, match="Cannot cancel order with status"):
        await order_service.cancel_order(order_id=1, user_id=200)


# ==================== List Orders Tests ====================


@pytest.mark.asyncio
async def test_list_buyer_orders(order_service, mock_order_repo, sample_order):
    """Test listing buyer orders"""
    # Setup
    mock_order_repo.list_by_buyer.return_value = [sample_order]
    mock_order_repo.count_by_buyer.return_value = 1
    
    # Execute
    orders, total = await order_service.list_buyer_orders(buyer_id=200, page=1, page_size=20)
    
    # Assert
    assert len(orders) == 1
    assert total == 1
    mock_order_repo.list_by_buyer.assert_called_once_with(buyer_id=200, offset=0, limit=20)


@pytest.mark.asyncio
async def test_list_seller_orders(order_service, mock_order_repo, sample_order):
    """Test listing seller orders"""
    # Setup
    mock_order_repo.list_by_seller.return_value = [sample_order]
    mock_order_repo.count_by_seller.return_value = 1
    
    # Execute
    orders, total = await order_service.list_seller_orders(seller_id=100, page=1, page_size=20)
    
    # Assert
    assert len(orders) == 1
    assert total == 1
    mock_order_repo.list_by_seller.assert_called_once_with(seller_id=100, offset=0, limit=20)


# ==================== Chat Entry Tests ====================


@pytest.mark.asyncio
async def test_get_chat_entry_as_buyer(order_service, mock_order_repo, sample_order):
    """Test getting chat entry as buyer"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute
    chat_entry = await order_service.get_chat_entry(order_id=1, user_id=200)
    
    # Assert
    assert chat_entry["order_id"] == 1
    assert chat_entry["other_party_id"] == 100  # Seller
    assert "conversation_id" in chat_entry
    assert "chat_url" in chat_entry


@pytest.mark.asyncio
async def test_get_chat_entry_as_seller(order_service, mock_order_repo, sample_order):
    """Test getting chat entry as seller"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute
    chat_entry = await order_service.get_chat_entry(order_id=1, user_id=100)
    
    # Assert
    assert chat_entry["order_id"] == 1
    assert chat_entry["other_party_id"] == 200  # Buyer


@pytest.mark.asyncio
async def test_get_chat_entry_permission_denied(order_service, mock_order_repo, sample_order):
    """Test getting chat entry fails when user is not buyer or seller"""
    # Setup
    mock_order_repo.get_by_id.return_value = sample_order
    
    # Execute & Assert
    with pytest.raises(PermissionDeniedError, match="You can only access chat for your own orders"):
        await order_service.get_chat_entry(order_id=1, user_id=999)
