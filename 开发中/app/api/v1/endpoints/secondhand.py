"""
Secondhand Items API Endpoints

Handles secondhand item CRUD operations, publishing, and file uploads.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import uuid

from app.core.database import get_mysql_session, get_redis
from app.core.dependencies import get_current_user
from app.core.permissions import require_verified
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, PermissionDeniedError, ResourceNotFoundError
from app.repositories.secondhand import SecondhandItemRepository, SecondhandOrderRepository
from app.repositories.user import UserRepository
from app.services.secondhand import SecondhandItemService, SecondhandOrderService
from app.services.content_audit import ContentAuditEngine
from app.services.sensitive_word import SensitiveWordService
from app.schemas.secondhand import (
    ItemCreate,
    ItemUpdate,
    ItemResponse,
    ItemListResponse,
    UploadResponse,
    item_to_response,
    OrderCreate,
    OrderResponse,
    OrderListResponse,
    OrderCancelRequest,
    ChatEntryResponse,
    order_to_response,
)
from app.models.user import User

router = APIRouter(prefix="/secondhand", tags=["secondhand"])


# ==================== Dependencies ====================


async def get_secondhand_service(
    session: AsyncSession = Depends(get_mysql_session),
    redis: Redis = Depends(get_redis)
) -> SecondhandItemService:
    """Get secondhand item service instance"""
    item_repo = SecondhandItemRepository(session)
    order_repo = SecondhandOrderRepository(session)
    sensitive_word_service = SensitiveWordService(redis)
    audit_engine = ContentAuditEngine(sensitive_word_service, redis)
    return SecondhandItemService(item_repo, order_repo, audit_engine, redis)


async def get_order_service(
    session: AsyncSession = Depends(get_mysql_session)
) -> SecondhandOrderService:
    """Get secondhand order service instance"""
    order_repo = SecondhandOrderRepository(session)
    item_repo = SecondhandItemRepository(session)
    return SecondhandOrderService(order_repo, item_repo)


async def get_user_repository(
    session: AsyncSession = Depends(get_mysql_session)
) -> UserRepository:
    """Get user repository instance"""
    return UserRepository(session)


async def get_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current verified user (dependency injection)"""
    from app.core.permissions import require_verified
    checker = require_verified()
    return checker(current_user)


# ==================== Item Endpoints ====================


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new secondhand item",
    description="Create a new secondhand item listing. Supports draft saving and automatic content audit."
)
async def create_item(
    item_data: ItemCreate,
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Create a new secondhand item
    
    - **title**: Item title (max 200 characters)
    - **description**: Item description
    - **category**: Item category (electronics, textbook, daily, sports, other)
    - **condition**: Item condition (brand_new, like_new, lightly_used, well_used, heavily_used)
    - **selling_price**: Selling price (must be > 0)
    - **original_price**: Optional original price
    - **images**: Optional list of image URLs (max 9)
    - **videos**: Optional list of video URLs (max 3)
    - **location**: Optional trading location
    - **is_negotiable**: Whether price is negotiable (default: false)
    - **delivery_method**: Delivery method (face_to_face, express, both)
    - **is_draft**: Whether to save as draft (default: false)
    """
    try:
        # Create item
        item = await secondhand_service.create_item(
            seller_id=current_user.id,
            school_id=current_user.school_id,
            title=item_data.title,
            description=item_data.description,
            category=item_data.category,
            condition=item_data.condition,
            selling_price=item_data.selling_price,
            original_price=item_data.original_price,
            images=item_data.images,
            videos=item_data.videos,
            location=item_data.location,
            is_negotiable=item_data.is_negotiable,
            delivery_method=item_data.delivery_method,
            is_draft=item_data.is_draft
        )
        
        # Get seller info
        seller_info = {
            "nickname": current_user.nickname,
            "avatar": current_user.avatar,
            "credit_score": current_user.credit_score
        }
        
        return success_response(
            data=item_to_response(item, seller_info),
            message="Item created successfully" if not item_data.is_draft else "Draft saved successfully"
        )
    
    except ValidationError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message=f"Failed to create item: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Get item by ID",
    description="Get detailed information about a specific secondhand item"
)
async def get_item(
    item_id: int,
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get item by ID
    
    - **item_id**: Item ID
    """
    try:
        item = await secondhand_service.get_item(item_id=item_id)
        
        # Get seller info
        seller = await user_repo.get_by_id(item.seller_id)
        seller_info = None
        if seller:
            seller_info = {
                "nickname": seller.nickname,
                "avatar": seller.avatar,
                "credit_score": seller.credit_score
            }
        
        return success_response(data=item_to_response(item, seller_info))
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message=f"Failed to get item: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Update item",
    description="Update an existing secondhand item (only by seller)"
)
async def update_item(
    item_id: int,
    item_data: ItemUpdate,
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Update item
    
    - **item_id**: Item ID
    - **title**: Optional new title
    - **description**: Optional new description
    - **selling_price**: Optional new selling price
    - **original_price**: Optional new original price
    - **images**: Optional new images
    - **videos**: Optional new videos
    - **location**: Optional new location
    - **is_negotiable**: Optional new negotiable flag
    - **delivery_method**: Optional new delivery method
    """
    try:
        item = await secondhand_service.update_item(
            item_id=item_id,
            seller_id=current_user.id,
            title=item_data.title,
            description=item_data.description,
            selling_price=item_data.selling_price,
            original_price=item_data.original_price,
            images=item_data.images,
            videos=item_data.videos,
            location=item_data.location,
            is_negotiable=item_data.is_negotiable,
            delivery_method=item_data.delivery_method
        )
        
        # Get seller info
        seller_info = {
            "nickname": current_user.nickname,
            "avatar": current_user.avatar,
            "credit_score": current_user.credit_score
        }
        
        return success_response(
            data=item_to_response(item, seller_info),
            message="Item updated successfully"
        )
    
    except (ResourceNotFoundError, PermissionDeniedError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to update item: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/items/{item_id}",
    summary="Delete item",
    description="Delete a secondhand item (only by seller, soft delete)"
)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service)
):
    """
    Delete item (soft delete)
    
    - **item_id**: Item ID
    """
    try:
        await secondhand_service.delete_item(item_id=item_id, seller_id=current_user.id)
        return success_response(message="Item deleted successfully")
    
    except (ResourceNotFoundError, PermissionDeniedError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to delete item: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/items/{item_id}/publish",
    response_model=ItemResponse,
    summary="Publish draft item",
    description="Publish a draft secondhand item"
)
async def publish_draft(
    item_id: int,
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Publish a draft item
    
    - **item_id**: Item ID
    """
    try:
        item = await secondhand_service.publish_draft(item_id=item_id, seller_id=current_user.id)
        
        # Get seller info
        seller_info = {
            "nickname": current_user.nickname,
            "avatar": current_user.avatar,
            "credit_score": current_user.credit_score
        }
        
        return success_response(
            data=item_to_response(item, seller_info),
            message="Draft published successfully"
        )
    
    except (ResourceNotFoundError, PermissionDeniedError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to publish draft: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/items",
    response_model=ItemListResponse,
    summary="List secondhand items",
    description="List secondhand items with filters"
)
async def list_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    keyword: Optional[str] = Query(None, description="Search keyword"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    List secondhand items with filters
    
    - **category**: Optional category filter (electronics, textbook, daily, sports, other)
    - **min_price**: Optional minimum price
    - **max_price**: Optional maximum price
    - **keyword**: Optional search keyword (searches title and description)
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    """
    try:
        if not current_user:
            return error_response(
                message="Authentication required",
                code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get items
        items, total = await secondhand_service.list_items(
            school_id=current_user.school_id,
            category=category,
            min_price=min_price,
            max_price=max_price,
            keyword=keyword,
            page=page,
            page_size=page_size
        )
        
        # Convert to response format
        item_responses = []
        for item in items:
            seller = await user_repo.get_by_id(item.seller_id)
            seller_info = None
            if seller:
                seller_info = {
                    "nickname": seller.nickname,
                    "avatar": seller.avatar,
                    "credit_score": seller.credit_score
                }
            item_responses.append(item_to_response(item, seller_info))
        
        return success_response(
            data=ItemListResponse(
                items=item_responses,
                total=total,
                page=page,
                page_size=page_size
            )
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to list items: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== Upload Endpoint (Placeholder) ====================


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload image or video (placeholder)",
    description="Placeholder endpoint for MinIO integration. Returns mock URLs for testing."
)
async def upload_file(
    file_type: str = Query(..., description="File type: image or video"),
    current_user: User = Depends(get_verified_user)
):
    """
    Upload image or video file (placeholder)
    
    This is a placeholder endpoint for MinIO integration.
    In production, this would:
    1. Accept file upload via multipart/form-data
    2. Validate file type and size
    3. Upload to MinIO object storage
    4. Return the permanent URL
    
    For now, it returns a mock URL for testing purposes.
    
    - **file_type**: File type (image or video)
    
    Note: Full file upload functionality requires MinIO integration.
    """
    try:
        # Validate file type
        if file_type not in ["image", "video"]:
            return error_response(
                message="File type must be 'image' or 'video'",
                code=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate mock URL (in production, upload to MinIO and get real URL)
        file_extension = "jpg" if file_type == "image" else "mp4"
        mock_url = f"https://cdn.zhiyu.com/{file_type}s/{uuid.uuid4()}.{file_extension}"
        
        return success_response(
            data=UploadResponse(
                url=mock_url,
                file_type=file_type,
                file_size=None  # Would be actual file size in production
            ),
            message="Mock URL generated successfully (MinIO integration pending)"
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to generate upload URL: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# ==================== Favorite Endpoints ====================


@router.post(
    "/items/{item_id}/favorite",
    summary="Toggle favorite status",
    description="Add or remove an item from favorites"
)
async def toggle_favorite(
    item_id: int,
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service)
):
    """
    Toggle favorite status for an item
    
    - **item_id**: Item ID
    
    Returns:
    - **is_favorited**: Whether the item is now favorited
    - **message**: Success message
    """
    try:
        is_favorited, message = await secondhand_service.toggle_favorite(
            user_id=current_user.id,
            item_id=item_id,
            school_id=current_user.school_id
        )
        
        return success_response(
            data={
                "item_id": item_id,
                "is_favorited": is_favorited
            },
            message=message
        )
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message=f"Failed to toggle favorite: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/favorites",
    response_model=ItemListResponse,
    summary="Get user's favorite items",
    description="Get list of items favorited by the current user"
)
async def get_favorites(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get user's favorite items
    
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    """
    try:
        items, total = await secondhand_service.get_user_favorites(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )
        
        # Convert to response format
        item_responses = []
        for item in items:
            seller = await user_repo.get_by_id(item.seller_id)
            seller_info = None
            if seller:
                seller_info = {
                    "nickname": seller.nickname,
                    "avatar": seller.avatar,
                    "credit_score": seller.credit_score
                }
            item_responses.append(item_to_response(item, seller_info))
        
        return success_response(
            data=ItemListResponse(
                items=item_responses,
                total=total,
                page=page,
                page_size=page_size
            )
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to get favorites: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/items/{item_id}/favorite-status",
    summary="Check favorite status",
    description="Check if current user has favorited an item"
)
async def check_favorite_status(
    item_id: int,
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service)
):
    """
    Check if user has favorited an item
    
    - **item_id**: Item ID
    """
    try:
        is_favorited = await secondhand_service.check_favorite_status(
            user_id=current_user.id,
            item_id=item_id
        )
        
        return success_response(
            data={
                "item_id": item_id,
                "is_favorited": is_favorited
            }
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to check favorite status: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== Price Alert Endpoints ====================


@router.post(
    "/items/{item_id}/price-alert",
    summary="Set price alert",
    description="Set or update price drop alert for an item"
)
async def set_price_alert(
    item_id: int,
    target_price: float = Query(..., gt=0, description="Target price for alert"),
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service)
):
    """
    Set or update price alert for an item
    
    - **item_id**: Item ID
    - **target_price**: Target price (must be lower than current price)
    
    The system will notify you when the item price drops to or below the target price.
    """
    try:
        alert_info = await secondhand_service.set_price_alert(
            user_id=current_user.id,
            item_id=item_id,
            school_id=current_user.school_id,
            target_price=target_price
        )
        
        return success_response(
            data=alert_info,
            message=alert_info["message"]
        )
    
    except (ResourceNotFoundError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to set price alert: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/items/{item_id}/price-alert",
    summary="Cancel price alert",
    description="Cancel price drop alert for an item"
)
async def cancel_price_alert(
    item_id: int,
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service)
):
    """
    Cancel price alert for an item
    
    - **item_id**: Item ID
    """
    try:
        deleted = await secondhand_service.cancel_price_alert(
            user_id=current_user.id,
            item_id=item_id
        )
        
        if deleted:
            return success_response(message="Price alert cancelled successfully")
        else:
            return error_response(
                message="Price alert not found",
                code=status.HTTP_404_NOT_FOUND
            )
    
    except Exception as e:
        return error_response(
            message=f"Failed to cancel price alert: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/price-alerts",
    summary="Get user's price alerts",
    description="Get list of price alerts set by the current user"
)
async def get_price_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_verified_user),
    secondhand_service: SecondhandItemService = Depends(get_secondhand_service)
):
    """
    Get user's price alerts
    
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    
    Returns list of alerts with item information and trigger status.
    """
    try:
        alerts, total = await secondhand_service.get_user_price_alerts(
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )
        
        return success_response(
            data={
                "alerts": alerts,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to get price alerts: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# ==================== Order Endpoints ====================


@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create order",
    description="Create a new order for a secondhand item (buyer initiates purchase)"
)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_verified_user),
    order_service: SecondhandOrderService = Depends(get_order_service)
):
    """
    Create a new order
    
    - **item_id**: Item ID to purchase
    - **delivery_method**: Delivery method (face_to_face or express)
    - **delivery_address**: Delivery address (required for express)
    - **buyer_note**: Optional buyer note
    
    Order flow:
    1. Buyer creates order → status: pending
    2. Seller confirms order → status: confirmed
    3. Face-to-face meeting and exchange
    4. Buyer confirms receipt → status: completed
    5. Item status changes to sold
    """
    try:
        order = await order_service.create_order(
            buyer_id=current_user.id,
            item_id=order_data.item_id,
            school_id=current_user.school_id,
            delivery_method=order_data.delivery_method,
            delivery_address=order_data.delivery_address,
            buyer_note=order_data.buyer_note,
        )
        
        return success_response(
            data=order_to_response(order),
            message="Order created successfully"
        )
    
    except (ResourceNotFoundError, ValidationError, PermissionDeniedError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to create order: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
    description="Get detailed information about a specific order"
)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_verified_user),
    order_service: SecondhandOrderService = Depends(get_order_service)
):
    """
    Get order by ID
    
    - **order_id**: Order ID
    
    Only buyer or seller can view the order.
    """
    try:
        order = await order_service.get_order(
            order_id=order_id,
            user_id=current_user.id
        )
        
        return success_response(data=order_to_response(order))
    
    except (ResourceNotFoundError, PermissionDeniedError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to get order: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put(
    "/orders/{order_id}/confirm",
    response_model=OrderResponse,
    summary="Confirm order",
    description="Confirm order (seller confirms)"
)
async def confirm_order(
    order_id: int,
    current_user: User = Depends(get_verified_user),
    order_service: SecondhandOrderService = Depends(get_order_service)
):
    """
    Confirm order (seller confirms)
    
    - **order_id**: Order ID
    
    Only the seller can confirm the order.
    Order status must be 'pending'.
    """
    try:
        order = await order_service.confirm_order(
            order_id=order_id,
            seller_id=current_user.id
        )
        
        return success_response(
            data=order_to_response(order),
            message="Order confirmed successfully"
        )
    
    except (ResourceNotFoundError, PermissionDeniedError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to confirm order: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put(
    "/orders/{order_id}/complete",
    response_model=OrderResponse,
    summary="Complete order",
    description="Complete order (buyer confirms receipt)"
)
async def complete_order(
    order_id: int,
    current_user: User = Depends(get_verified_user),
    order_service: SecondhandOrderService = Depends(get_order_service)
):
    """
    Complete order (buyer confirms receipt)
    
    - **order_id**: Order ID
    
    Only the buyer can complete the order.
    Order status must be 'confirmed'.
    After completion, the item status changes to 'sold'.
    """
    try:
        order = await order_service.complete_order(
            order_id=order_id,
            buyer_id=current_user.id
        )
        
        return success_response(
            data=order_to_response(order),
            message="Order completed successfully"
        )
    
    except (ResourceNotFoundError, PermissionDeniedError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to complete order: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put(
    "/orders/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel order",
    description="Cancel order (buyer or seller can cancel)"
)
async def cancel_order(
    order_id: int,
    cancel_data: OrderCancelRequest,
    current_user: User = Depends(get_verified_user),
    order_service: SecondhandOrderService = Depends(get_order_service)
):
    """
    Cancel order
    
    - **order_id**: Order ID
    - **cancel_reason**: Optional cancellation reason
    
    Both buyer and seller can cancel the order.
    Cannot cancel completed or already cancelled orders.
    """
    try:
        order = await order_service.cancel_order(
            order_id=order_id,
            user_id=current_user.id,
            cancel_reason=cancel_data.cancel_reason
        )
        
        return success_response(
            data=order_to_response(order),
            message="Order cancelled successfully"
        )
    
    except (ResourceNotFoundError, PermissionDeniedError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to cancel order: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="List orders",
    description="List orders (buyer or seller view)"
)
async def list_orders(
    view: str = Query("buyer", description="View type: buyer or seller"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_verified_user),
    order_service: SecondhandOrderService = Depends(get_order_service)
):
    """
    List orders
    
    - **view**: View type (buyer or seller)
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    
    Returns orders where the current user is either the buyer or seller,
    depending on the view parameter.
    """
    try:
        if view not in ["buyer", "seller"]:
            return error_response(
                message="View must be 'buyer' or 'seller'",
                code=status.HTTP_400_BAD_REQUEST
            )
        
        if view == "buyer":
            orders, total = await order_service.list_buyer_orders(
                buyer_id=current_user.id,
                page=page,
                page_size=page_size
            )
        else:
            orders, total = await order_service.list_seller_orders(
                seller_id=current_user.id,
                page=page,
                page_size=page_size
            )
        
        order_responses = [order_to_response(order) for order in orders]
        
        return success_response(
            data=OrderListResponse(
                orders=order_responses,
                total=total,
                page=page,
                page_size=page_size
            )
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to list orders: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/orders/{order_id}/chat",
    response_model=ChatEntryResponse,
    summary="Get IM chat entry",
    description="Get IM chat entry for order communication (placeholder for future IM integration)"
)
async def get_chat_entry(
    order_id: int,
    current_user: User = Depends(get_verified_user),
    order_service: SecondhandOrderService = Depends(get_order_service)
):
    """
    Get IM chat entry for order
    
    - **order_id**: Order ID
    
    This is a placeholder endpoint for future IM integration.
    It returns mock chat entry information for testing purposes.
    
    In production, this would:
    1. Create or retrieve a conversation between buyer and seller
    2. Return the conversation ID and chat URL
    3. Allow real-time messaging through WebSocket
    
    Only buyer or seller can access the chat.
    """
    try:
        chat_entry = await order_service.get_chat_entry(
            order_id=order_id,
            user_id=current_user.id
        )
        
        return success_response(
            data=ChatEntryResponse(**chat_entry),
            message="Chat entry retrieved (IM integration pending)"
        )
    
    except (ResourceNotFoundError, PermissionDeniedError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to get chat entry: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
