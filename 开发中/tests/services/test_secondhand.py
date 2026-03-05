"""
Tests for Secondhand Item Service

Tests for secondhand item creation, publishing, and management.
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.services.secondhand import SecondhandItemService, PROHIBITED_KEYWORDS
from app.models.secondhand import SecondhandItem, ItemStatus, ItemCategory, ItemCondition, DeliveryMethod
from app.core.exceptions import ValidationError, PermissionDeniedError, ResourceNotFoundError


@pytest.fixture
def mock_item_repo():
    """Mock item repository"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_order_repo():
    """Mock order repository"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_audit_engine():
    """Mock audit engine"""
    engine = AsyncMock()
    # Default: audit passes
    engine.audit_content = AsyncMock(return_value=MagicMock(
        to_dict=lambda: {
            "passed": True,
            "action": "approve",
            "reason": None,
            "found_words": [],
            "confidence": 1.0
        }
    ))
    return engine


@pytest.fixture
def secondhand_service(mock_item_repo, mock_order_repo, mock_audit_engine):
    """Create secondhand service instance"""
    return SecondhandItemService(
        item_repository=mock_item_repo,
        order_repository=mock_order_repo,
        audit_engine=mock_audit_engine,
        redis=None
    )


# ==================== Item Creation Tests ====================


@pytest.mark.asyncio
async def test_create_item_success(secondhand_service, mock_item_repo):
    """Test successful item creation"""
    # Arrange
    mock_item = SecondhandItem(
        id=1,
        seller_id=1,
        school_id=1,
        title="Test Item",
        description="Test description",
        category=ItemCategory.ELECTRONICS,
        condition=ItemCondition.LIKE_NEW,
        selling_price=Decimal("100.00"),
        original_price=Decimal("200.00"),
        images={"urls": ["http://example.com/image1.jpg"]},
        videos=None,
        location="Campus A",
        is_negotiable=True,
        delivery_method=DeliveryMethod.FACE_TO_FACE,
        status=ItemStatus.ON_SALE
    )
    mock_item_repo.create = AsyncMock(return_value=mock_item)
    
    # Act
    result = await secondhand_service.create_item(
        seller_id=1,
        school_id=1,
        title="Test Item",
        description="Test description",
        category="electronics",
        condition="like_new",
        selling_price=Decimal("100.00"),
        original_price=Decimal("200.00"),
        images=["http://example.com/image1.jpg"],
        videos=None,
        location="Campus A",
        is_negotiable=True,
        delivery_method="face_to_face",
        is_draft=False
    )
    
    # Assert
    assert result.id == 1
    assert result.title == "Test Item"
    assert result.status == ItemStatus.ON_SALE
    mock_item_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_item_as_draft(secondhand_service, mock_item_repo):
    """Test creating item as draft (no audit)"""
    # Arrange
    mock_item = SecondhandItem(
        id=1,
        seller_id=1,
        school_id=1,
        title="Draft Item",
        description="Draft description",
        category=ItemCategory.TEXTBOOK,
        condition=ItemCondition.BRAND_NEW,
        selling_price=Decimal("50.00"),
        original_price=None,
        images=None,
        videos=None,
        location=None,
        is_negotiable=False,
        delivery_method=DeliveryMethod.EXPRESS,
        status=ItemStatus.DRAFT
    )
    mock_item_repo.create = AsyncMock(return_value=mock_item)
    
    # Act
    result = await secondhand_service.create_item(
        seller_id=1,
        school_id=1,
        title="Draft Item",
        description="Draft description",
        category="textbook",
        condition="brand_new",
        selling_price=Decimal("50.00"),
        original_price=None,
        images=None,
        videos=None,
        location=None,
        is_negotiable=False,
        delivery_method="express",
        is_draft=True
    )
    
    # Assert
    assert result.status == ItemStatus.DRAFT
    # Audit should not be called for drafts
    mock_item_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_item_empty_title_fails(secondhand_service):
    """Test that empty title fails validation"""
    # Act & Assert
    with pytest.raises(ValidationError, match="Title is required"):
        await secondhand_service.create_item(
            seller_id=1,
            school_id=1,
            title="",
            description="Test",
            category="electronics",
            condition="like_new",
            selling_price=Decimal("100.00"),
            original_price=None,
            images=None,
            videos=None,
            location=None,
            is_negotiable=False,
            delivery_method="face_to_face",
            is_draft=False
        )


@pytest.mark.asyncio
async def test_create_item_title_too_long_fails(secondhand_service):
    """Test that title exceeding 200 characters fails"""
    # Act & Assert
    with pytest.raises(ValidationError, match="Title cannot exceed 200 characters"):
        await secondhand_service.create_item(
            seller_id=1,
            school_id=1,
            title="a" * 201,
            description="Test",
            category="electronics",
            condition="like_new",
            selling_price=Decimal("100.00"),
            original_price=None,
            images=None,
            videos=None,
            location=None,
            is_negotiable=False,
            delivery_method="face_to_face",
            is_draft=False
        )


@pytest.mark.asyncio
async def test_create_item_negative_price_fails(secondhand_service):
    """Test that negative price fails validation"""
    # Act & Assert
    with pytest.raises(ValidationError, match="Selling price must be greater than 0"):
        await secondhand_service.create_item(
            seller_id=1,
            school_id=1,
            title="Test Item",
            description="Test",
            category="electronics",
            condition="like_new",
            selling_price=Decimal("-10.00"),
            original_price=None,
            images=None,
            videos=None,
            location=None,
            is_negotiable=False,
            delivery_method="face_to_face",
            is_draft=False
        )


@pytest.mark.asyncio
async def test_create_item_original_price_less_than_selling_fails(secondhand_service):
    """Test that original price less than selling price fails"""
    # Act & Assert
    with pytest.raises(ValidationError, match="Original price cannot be less than selling price"):
        await secondhand_service.create_item(
            seller_id=1,
            school_id=1,
            title="Test Item",
            description="Test",
            category="electronics",
            condition="like_new",
            selling_price=Decimal("100.00"),
            original_price=Decimal("50.00"),
            images=None,
            videos=None,
            location=None,
            is_negotiable=False,
            delivery_method="face_to_face",
            is_draft=False
        )


@pytest.mark.asyncio
async def test_create_item_too_many_images_fails(secondhand_service):
    """Test that more than 9 images fails validation"""
    # Act & Assert
    with pytest.raises(ValidationError, match="Maximum 9 images allowed"):
        await secondhand_service.create_item(
            seller_id=1,
            school_id=1,
            title="Test Item",
            description="Test",
            category="electronics",
            condition="like_new",
            selling_price=Decimal("100.00"),
            original_price=None,
            images=[f"http://example.com/image{i}.jpg" for i in range(10)],
            videos=None,
            location=None,
            is_negotiable=False,
            delivery_method="face_to_face",
            is_draft=False
        )


@pytest.mark.asyncio
async def test_create_item_too_many_videos_fails(secondhand_service):
    """Test that more than 3 videos fails validation"""
    # Act & Assert
    with pytest.raises(ValidationError, match="Maximum 3 videos allowed"):
        await secondhand_service.create_item(
            seller_id=1,
            school_id=1,
            title="Test Item",
            description="Test",
            category="electronics",
            condition="like_new",
            selling_price=Decimal("100.00"),
            original_price=None,
            images=None,
            videos=[f"http://example.com/video{i}.mp4" for i in range(4)],
            location=None,
            is_negotiable=False,
            delivery_method="face_to_face",
            is_draft=False
        )


@pytest.mark.asyncio
async def test_create_item_invalid_category_fails(secondhand_service):
    """Test that invalid category fails validation"""
    # Act & Assert
    with pytest.raises(ValidationError, match="Invalid category"):
        await secondhand_service.create_item(
            seller_id=1,
            school_id=1,
            title="Test Item",
            description="Test",
            category="invalid_category",
            condition="like_new",
            selling_price=Decimal("100.00"),
            original_price=None,
            images=None,
            videos=None,
            location=None,
            is_negotiable=False,
            delivery_method="face_to_face",
            is_draft=False
        )


# ==================== Prohibited Items Tests ====================


@pytest.mark.asyncio
async def test_create_item_with_prohibited_keyword_fails(secondhand_service, mock_audit_engine):
    """Test that items with prohibited keywords are blocked"""
    # Arrange
    # Mock audit to detect prohibited item
    mock_audit_engine.audit_content = AsyncMock(return_value=MagicMock(
        to_dict=lambda: {
            "passed": False,
            "action": "block",
            "reason": "检测到违禁品关键词: 武器",
            "found_words": ["武器"],
            "confidence": 1.0
        }
    ))
    
    # Act & Assert
    with pytest.raises(ValidationError, match="prohibited items or sensitive words"):
        await secondhand_service.create_item(
            seller_id=1,
            school_id=1,
            title="出售武器模型",
            description="全新武器模型",
            category="other",
            condition="brand_new",
            selling_price=Decimal("100.00"),
            original_price=None,
            images=None,
            videos=None,
            location=None,
            is_negotiable=False,
            delivery_method="face_to_face",
            is_draft=False
        )


# ==================== Publish Draft Tests ====================


@pytest.mark.asyncio
async def test_publish_draft_success(secondhand_service, mock_item_repo):
    """Test successful draft publishing"""
    # Arrange
    mock_item = SecondhandItem(
        id=1,
        seller_id=1,
        school_id=1,
        title="Draft Item",
        description="Draft description",
        category=ItemCategory.TEXTBOOK,
        condition=ItemCondition.BRAND_NEW,
        selling_price=Decimal("50.00"),
        original_price=None,
        images=None,
        videos=None,
        location=None,
        is_negotiable=False,
        delivery_method=DeliveryMethod.EXPRESS,
        status=ItemStatus.DRAFT
    )
    mock_item_repo.get_by_id = AsyncMock(return_value=mock_item)
    mock_item_repo.update = AsyncMock(return_value=mock_item)
    
    # Act
    result = await secondhand_service.publish_draft(item_id=1, seller_id=1)
    
    # Assert
    assert result.status == ItemStatus.ON_SALE
    mock_item_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_publish_draft_not_found_fails(secondhand_service, mock_item_repo):
    """Test publishing non-existent draft fails"""
    # Arrange
    mock_item_repo.get_by_id = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match="Item 999 not found"):
        await secondhand_service.publish_draft(item_id=999, seller_id=1)


@pytest.mark.asyncio
async def test_publish_draft_wrong_seller_fails(secondhand_service, mock_item_repo):
    """Test publishing draft by non-owner fails"""
    # Arrange
    mock_item = SecondhandItem(
        id=1,
        seller_id=1,
        school_id=1,
        title="Draft Item",
        description="Draft description",
        category=ItemCategory.TEXTBOOK,
        condition=ItemCondition.BRAND_NEW,
        selling_price=Decimal("50.00"),
        original_price=None,
        images=None,
        videos=None,
        location=None,
        is_negotiable=False,
        delivery_method=DeliveryMethod.EXPRESS,
        status=ItemStatus.DRAFT
    )
    mock_item_repo.get_by_id = AsyncMock(return_value=mock_item)
    
    # Act & Assert
    with pytest.raises(PermissionDeniedError, match="You can only publish your own drafts"):
        await secondhand_service.publish_draft(item_id=1, seller_id=999)


@pytest.mark.asyncio
async def test_publish_non_draft_fails(secondhand_service, mock_item_repo):
    """Test publishing non-draft item fails"""
    # Arrange
    mock_item = SecondhandItem(
        id=1,
        seller_id=1,
        school_id=1,
        title="Published Item",
        description="Already published",
        category=ItemCategory.TEXTBOOK,
        condition=ItemCondition.BRAND_NEW,
        selling_price=Decimal("50.00"),
        original_price=None,
        images=None,
        videos=None,
        location=None,
        is_negotiable=False,
        delivery_method=DeliveryMethod.EXPRESS,
        status=ItemStatus.ON_SALE
    )
    mock_item_repo.get_by_id = AsyncMock(return_value=mock_item)
    
    # Act & Assert
    with pytest.raises(ValidationError, match="Only draft items can be published"):
        await secondhand_service.publish_draft(item_id=1, seller_id=1)


# ==================== Get Item Tests ====================


@pytest.mark.asyncio
async def test_get_item_success(secondhand_service, mock_item_repo):
    """Test successful item retrieval"""
    # Arrange
    mock_item = SecondhandItem(
        id=1,
        seller_id=1,
        school_id=1,
        title="Test Item",
        description="Test description",
        category=ItemCategory.ELECTRONICS,
        condition=ItemCondition.LIKE_NEW,
        selling_price=Decimal("100.00"),
        original_price=None,
        images=None,
        videos=None,
        location=None,
        is_negotiable=False,
        delivery_method=DeliveryMethod.FACE_TO_FACE,
        status=ItemStatus.ON_SALE
    )
    mock_item_repo.get_by_id = AsyncMock(return_value=mock_item)
    mock_item_repo.increment_view_count = AsyncMock()
    
    # Act
    result = await secondhand_service.get_item(item_id=1)
    
    # Assert
    assert result.id == 1
    assert result.title == "Test Item"
    mock_item_repo.increment_view_count.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_item_not_found_fails(secondhand_service, mock_item_repo):
    """Test getting non-existent item fails"""
    # Arrange
    mock_item_repo.get_by_id = AsyncMock(return_value=None)
    
    # Act & Assert
    with pytest.raises(ResourceNotFoundError, match="Item 999 not found"):
        await secondhand_service.get_item(item_id=999)


# ==================== Delete Item Tests ====================


@pytest.mark.asyncio
async def test_delete_item_success(secondhand_service, mock_item_repo):
    """Test successful item deletion"""
    # Arrange
    mock_item = SecondhandItem(
        id=1,
        seller_id=1,
        school_id=1,
        title="Test Item",
        description="Test description",
        category=ItemCategory.ELECTRONICS,
        condition=ItemCondition.LIKE_NEW,
        selling_price=Decimal("100.00"),
        original_price=None,
        images=None,
        videos=None,
        location=None,
        is_negotiable=False,
        delivery_method=DeliveryMethod.FACE_TO_FACE,
        status=ItemStatus.ON_SALE
    )
    mock_item_repo.get_by_id = AsyncMock(return_value=mock_item)
    mock_item_repo.delete = AsyncMock()
    
    # Act
    result = await secondhand_service.delete_item(item_id=1, seller_id=1)
    
    # Assert
    assert result is True
    mock_item_repo.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_item_wrong_seller_fails(secondhand_service, mock_item_repo):
    """Test deleting item by non-owner fails"""
    # Arrange
    mock_item = SecondhandItem(
        id=1,
        seller_id=1,
        school_id=1,
        title="Test Item",
        description="Test description",
        category=ItemCategory.ELECTRONICS,
        condition=ItemCondition.LIKE_NEW,
        selling_price=Decimal("100.00"),
        original_price=None,
        images=None,
        videos=None,
        location=None,
        is_negotiable=False,
        delivery_method=DeliveryMethod.FACE_TO_FACE,
        status=ItemStatus.ON_SALE
    )
    mock_item_repo.get_by_id = AsyncMock(return_value=mock_item)
    
    # Act & Assert
    with pytest.raises(PermissionDeniedError, match="You can only delete your own items"):
        await secondhand_service.delete_item(item_id=1, seller_id=999)
