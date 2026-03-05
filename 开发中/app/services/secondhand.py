"""
Secondhand Item Service

Business logic for secondhand item publishing, management, and transactions.
"""
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
from redis.asyncio import Redis

from app.repositories.secondhand import SecondhandItemRepository, SecondhandOrderRepository
from app.services.content_audit import ContentAuditEngine
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
    ResourceNotFoundError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


# Prohibited items keywords (违禁品关键词)
PROHIBITED_KEYWORDS = [
    # 武器、管制刀具
    "武器", "枪", "刀具", "管制刀", "匕首", "弹药",
    # 毒品、药品
    "毒品", "大麻", "海洛因", "冰毒", "处方药", "麻醉药",
    # 假货、盗版
    "假货", "高仿", "A货", "盗版", "山寨",
    # 烟草、酒精
    "香烟", "烟草", "白酒", "啤酒", "红酒",
    # 活体动物
    "活体", "宠物买卖",
    # 身份证件
    "身份证", "护照", "驾驶证", "学生证买卖",
    # 考试答案
    "考试答案", "作弊器", "替考",
]


class SecondhandItemService:
    """Service for secondhand item operations"""
    
    def __init__(
        self,
        item_repository: SecondhandItemRepository,
        order_repository: SecondhandOrderRepository,
        audit_engine: ContentAuditEngine,
        redis: Optional[Redis] = None
    ):
        self.item_repo = item_repository
        self.order_repo = order_repository
        self.audit_engine = audit_engine
        self.redis = redis
        
        # Redis cache TTL (5 minutes)
        self.cache_ttl = 300
    
    async def create_item(
        self,
        seller_id: int,
        school_id: int,
        title: str,
        description: Optional[str],
        category: str,
        condition: str,
        selling_price: Decimal,
        original_price: Optional[Decimal],
        images: Optional[List[str]],
        videos: Optional[List[str]],
        location: Optional[str],
        is_negotiable: bool,
        delivery_method: str,
        is_draft: bool = False
    ) -> SecondhandItem:
        """
        Create a new secondhand item
        
        Args:
            seller_id: Seller user ID
            school_id: School ID
            title: Item title
            description: Item description
            category: Item category
            condition: Item condition
            selling_price: Selling price
            original_price: Original price
            images: List of image URLs
            videos: List of video URLs
            location: Trading location
            is_negotiable: Whether price is negotiable
            delivery_method: Delivery method
            is_draft: Whether to save as draft
        
        Returns:
            Created secondhand item
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        if not title or len(title.strip()) == 0:
            raise ValidationError("Title is required")
        
        if len(title) > 200:
            raise ValidationError("Title cannot exceed 200 characters")
        
        if selling_price <= 0:
            raise ValidationError("Selling price must be greater than 0")
        
        if original_price and original_price < selling_price:
            raise ValidationError("Original price cannot be less than selling price")
        
        # Validate category
        try:
            ItemCategory(category)
        except ValueError:
            raise ValidationError(f"Invalid category: {category}")
        
        # Validate condition
        try:
            ItemCondition(condition)
        except ValueError:
            raise ValidationError(f"Invalid condition: {condition}")
        
        # Validate delivery method
        try:
            DeliveryMethod(delivery_method)
        except ValueError:
            raise ValidationError(f"Invalid delivery method: {delivery_method}")
        
        # Validate images and videos
        if images and len(images) > 9:
            raise ValidationError("Maximum 9 images allowed")
        
        if videos and len(videos) > 3:
            raise ValidationError("Maximum 3 videos allowed")
        
        # Determine initial status
        if is_draft:
            status = ItemStatus.DRAFT
            audit_result = None
        else:
            # Audit content before publishing
            audit_result = await self._audit_item_content(
                title=title,
                description=description or "",
                images=images or []
            )
            
            if audit_result["action"] == "block":
                raise ValidationError(
                    f"Content contains prohibited items or sensitive words: {', '.join(audit_result['found_words'])}"
                )
            
            status = ItemStatus.ON_SALE
        
        # Create item
        item = SecondhandItem(
            seller_id=seller_id,
            school_id=school_id,
            title=title,
            description=description,
            category=ItemCategory(category),
            condition=ItemCondition(condition),
            selling_price=selling_price,
            original_price=original_price,
            images={"urls": images} if images else None,
            videos={"urls": videos} if videos else None,
            location=location,
            is_negotiable=is_negotiable,
            delivery_method=DeliveryMethod(delivery_method),
            status=status,
        )
        
        created_item = await self.item_repo.create(item)
        
        logger.info(
            "Secondhand item created",
            item_id=created_item.id,
            seller_id=seller_id,
            school_id=school_id,
            status=status.value,
            is_draft=is_draft
        )
        
        return created_item
    
    async def _audit_item_content(
        self,
        title: str,
        description: str,
        images: List[str]
    ) -> Dict:
        """
        Audit item content for prohibited items and sensitive words
        
        Args:
            title: Item title
            description: Item description
            images: Image URLs
        
        Returns:
            Audit result dictionary
        """
        # Combine title and description for text audit
        full_text = f"{title}\n{description}"
        
        # First check for prohibited items
        found_prohibited = []
        full_text_lower = full_text.lower()
        for keyword in PROHIBITED_KEYWORDS:
            if keyword in full_text_lower:
                found_prohibited.append(keyword)
        
        if found_prohibited:
            return {
                "passed": False,
                "action": "block",
                "reason": f"检测到违禁品关键词: {', '.join(found_prohibited)}",
                "found_words": found_prohibited,
                "confidence": 1.0
            }
        
        # Then audit for general sensitive words
        audit_result = await self.audit_engine.audit_content(
            text=full_text,
            images=images if images else None,
            strict_mode=True  # Use strict mode for secondhand items
        )
        
        return audit_result.to_dict()
    
    async def publish_draft(self, item_id: int, seller_id: int) -> SecondhandItem:
        """
        Publish a draft item
        
        Args:
            item_id: Item ID
            seller_id: Seller ID (must be the owner)
        
        Returns:
            Published item
        
        Raises:
            ResourceNotFoundError: If item not found
            PermissionDeniedError: If user is not the seller
            ValidationError: If item is not a draft
        """
        # Get item
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError(f"Item {item_id} not found")
        
        # Check permission
        if item.seller_id != seller_id:
            raise PermissionDeniedError("You can only publish your own drafts")
        
        # Check if draft
        if item.status != ItemStatus.DRAFT:
            raise ValidationError("Only draft items can be published")
        
        # Audit content
        audit_result = await self._audit_item_content(
            title=item.title,
            description=item.description or "",
            images=item.images.get("urls", []) if item.images else []
        )
        
        if audit_result["action"] == "block":
            raise ValidationError(
                f"Content contains prohibited items or sensitive words: {', '.join(audit_result['found_words'])}"
            )
        
        # Update status
        item.status = ItemStatus.ON_SALE
        updated_item = await self.item_repo.update(item)
        
        logger.info(
            "Draft item published",
            item_id=item_id,
            seller_id=seller_id
        )
        
        return updated_item
    
    async def get_item(self, item_id: int) -> SecondhandItem:
        """
        Get item by ID and increment view count
        
        Args:
            item_id: Item ID
        
        Returns:
            Secondhand item
        
        Raises:
            ResourceNotFoundError: If item not found
        """
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError(f"Item {item_id} not found")
        
        # Increment view count (async, don't wait)
        await self.item_repo.increment_view_count(item_id)
        
        return item
    
    async def update_item(
        self,
        item_id: int,
        seller_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        selling_price: Optional[Decimal] = None,
        original_price: Optional[Decimal] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        location: Optional[str] = None,
        is_negotiable: Optional[bool] = None,
        delivery_method: Optional[str] = None
    ) -> SecondhandItem:
        """
        Update an item
        
        Args:
            item_id: Item ID
            seller_id: Seller ID (must be the owner)
            title: New title
            description: New description
            selling_price: New selling price
            original_price: New original price
            images: New images
            videos: New videos
            location: New location
            is_negotiable: New negotiable flag
            delivery_method: New delivery method
        
        Returns:
            Updated item
        
        Raises:
            ResourceNotFoundError: If item not found
            PermissionDeniedError: If user is not the seller
            ValidationError: If validation fails
        """
        # Get item
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError(f"Item {item_id} not found")
        
        # Check permission
        if item.seller_id != seller_id:
            raise PermissionDeniedError("You can only update your own items")
        
        # Update fields
        if title is not None:
            if len(title) > 200:
                raise ValidationError("Title cannot exceed 200 characters")
            item.title = title
        
        if description is not None:
            item.description = description
        
        if selling_price is not None:
            if selling_price <= 0:
                raise ValidationError("Selling price must be greater than 0")
            item.selling_price = selling_price
        
        if original_price is not None:
            if original_price < item.selling_price:
                raise ValidationError("Original price cannot be less than selling price")
            item.original_price = original_price
        
        if images is not None:
            if len(images) > 9:
                raise ValidationError("Maximum 9 images allowed")
            item.images = {"urls": images}
        
        if videos is not None:
            if len(videos) > 3:
                raise ValidationError("Maximum 3 videos allowed")
            item.videos = {"urls": videos}
        
        if location is not None:
            item.location = location
        
        if is_negotiable is not None:
            item.is_negotiable = is_negotiable
        
        if delivery_method is not None:
            try:
                item.delivery_method = DeliveryMethod(delivery_method)
            except ValueError:
                raise ValidationError(f"Invalid delivery method: {delivery_method}")
        
        # If content changed and item is on sale, re-audit
        if (title is not None or description is not None) and item.status == ItemStatus.ON_SALE:
            audit_result = await self._audit_item_content(
                title=item.title,
                description=item.description or "",
                images=item.images.get("urls", []) if item.images else []
            )
            
            if audit_result["action"] == "block":
                raise ValidationError(
                    f"Content contains prohibited items or sensitive words: {', '.join(audit_result['found_words'])}"
                )
        
        # Update item
        updated_item = await self.item_repo.update(item)
        
        # Check if price was updated and trigger alerts
        if selling_price is not None:
            await self.check_and_trigger_price_alerts(item_id)
        
        logger.info(
            "Item updated",
            item_id=item_id,
            seller_id=seller_id
        )
        
        return updated_item
    
    async def delete_item(self, item_id: int, seller_id: int) -> bool:
        """
        Delete an item (soft delete)
        
        Args:
            item_id: Item ID
            seller_id: Seller ID (must be the owner)
        
        Returns:
            True if deleted
        
        Raises:
            ResourceNotFoundError: If item not found
            PermissionDeniedError: If user is not the seller
        """
        # Get item
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError(f"Item {item_id} not found")
        
        # Check permission
        if item.seller_id != seller_id:
            raise PermissionDeniedError("You can only delete your own items")
        
        # Delete item (soft delete)
        await self.item_repo.delete(item)
        
        logger.info("Item deleted", item_id=item_id, seller_id=seller_id)
        
        return True
    
    async def list_items(
        self,
        school_id: int,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[SecondhandItem], int]:
        """
        List items with filters
        
        Args:
            school_id: School ID (for data isolation)
            category: Optional category filter
            min_price: Optional minimum price
            max_price: Optional maximum price
            keyword: Optional keyword search
            page: Page number (1-indexed)
            page_size: Number of items per page
        
        Returns:
            Tuple of (list of items, total count)
        """
        offset = (page - 1) * page_size
        
        items = await self.item_repo.search(
            school_id=school_id,
            keyword=keyword,
            category=category,
            min_price=min_price,
            max_price=max_price,
            offset=offset,
            limit=page_size
        )
        
        # TODO: Add total count query
        total = len(items)
        
        logger.info(
            "Listed items",
            school_id=school_id,
            category=category,
            page=page,
            page_size=page_size,
            count=len(items)
        )
        
        return items, total
    
    async def list_seller_items(
        self,
        seller_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[SecondhandItem]:
        """
        List items by seller
        
        Args:
            seller_id: Seller ID
            page: Page number (1-indexed)
            page_size: Number of items per page
        
        Returns:
            List of items
        """
        offset = (page - 1) * page_size
        items = await self.item_repo.list_by_seller(
            seller_id=seller_id,
            offset=offset,
            limit=page_size
        )
        return items


    async def toggle_favorite(
        self,
        user_id: int,
        item_id: int,
        school_id: int
    ) -> tuple[bool, str]:
        """
        Toggle favorite status for an item
        
        Args:
            user_id: User ID
            item_id: Item ID
            school_id: School ID
        
        Returns:
            Tuple of (is_favorited, message)
        
        Raises:
            ResourceNotFoundError: If item not found
        """
        from app.repositories.secondhand import ItemFavoriteRepository
        
        # Check if item exists
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError(f"Item {item_id} not found")
        
        # Create favorite repository
        favorite_repo = ItemFavoriteRepository(self.item_repo.session)
        
        # Check if already favorited
        exists = await favorite_repo.exists(user_id, item_id)
        
        if exists:
            # Unfavorite
            await favorite_repo.delete(user_id, item_id)
            await self.item_repo.decrement_favorite_count(item_id)
            
            logger.info(
                "Item unfavorited",
                user_id=user_id,
                item_id=item_id
            )
            
            return False, "Item removed from favorites"
        else:
            # Favorite
            await favorite_repo.create(user_id, item_id, school_id)
            await self.item_repo.increment_favorite_count(item_id)
            
            logger.info(
                "Item favorited",
                user_id=user_id,
                item_id=item_id
            )
            
            return True, "Item added to favorites"
    
    async def get_user_favorites(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[SecondhandItem], int]:
        """
        Get user's favorite items
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of items per page
        
        Returns:
            Tuple of (list of items, total count)
        """
        from app.repositories.secondhand import ItemFavoriteRepository
        
        favorite_repo = ItemFavoriteRepository(self.item_repo.session)
        
        offset = (page - 1) * page_size
        favorites = await favorite_repo.list_by_user(
            user_id=user_id,
            offset=offset,
            limit=page_size
        )
        
        # Get items
        items = []
        for favorite in favorites:
            item = await self.item_repo.get_by_id(favorite.item_id)
            if item:
                items.append(item)
        
        # Get total count
        total = await favorite_repo.count_by_user(user_id)
        
        logger.info(
            "Listed user favorites",
            user_id=user_id,
            page=page,
            page_size=page_size,
            count=len(items)
        )
        
        return items, total
    
    async def check_favorite_status(
        self,
        user_id: int,
        item_id: int
    ) -> bool:
        """
        Check if user has favorited an item
        
        Args:
            user_id: User ID
            item_id: Item ID
        
        Returns:
            bool: True if favorited, False otherwise
        """
        from app.repositories.secondhand import ItemFavoriteRepository
        
        favorite_repo = ItemFavoriteRepository(self.item_repo.session)
        return await favorite_repo.exists(user_id, item_id)
    
    async def set_price_alert(
        self,
        user_id: int,
        item_id: int,
        school_id: int,
        target_price: float
    ) -> dict:
        """
        Set or update price alert for an item
        
        Args:
            user_id: User ID
            item_id: Item ID
            school_id: School ID
            target_price: Target price for alert
        
        Returns:
            dict: Alert information
        
        Raises:
            ResourceNotFoundError: If item not found
            ValidationError: If target price is invalid
        """
        from app.repositories.secondhand import PriceAlertRepository
        from decimal import Decimal
        
        # Check if item exists
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError(f"Item {item_id} not found")
        
        # Validate target price
        if target_price <= 0:
            raise ValidationError("Target price must be greater than 0")
        
        if target_price >= float(item.selling_price):
            raise ValidationError("Target price must be lower than current price")
        
        # Create alert repository
        alert_repo = PriceAlertRepository(self.item_repo.session)
        
        # Check if alert already exists
        existing_alert = await alert_repo.get_by_user_and_item(user_id, item_id)
        
        if existing_alert:
            # Update existing alert
            existing_alert.target_price = Decimal(str(target_price))
            existing_alert.is_active = True
            existing_alert.notified_at = None
            await alert_repo.update(existing_alert)
            
            logger.info(
                "Price alert updated",
                user_id=user_id,
                item_id=item_id,
                target_price=target_price
            )
            
            return {
                "alert_id": existing_alert.id,
                "item_id": item_id,
                "target_price": float(existing_alert.target_price),
                "current_price": float(item.selling_price),
                "is_active": existing_alert.is_active,
                "message": "Price alert updated successfully"
            }
        else:
            # Create new alert
            alert = await alert_repo.create(
                user_id=user_id,
                item_id=item_id,
                school_id=school_id,
                target_price=target_price
            )
            
            logger.info(
                "Price alert created",
                user_id=user_id,
                item_id=item_id,
                target_price=target_price
            )
            
            return {
                "alert_id": alert.id,
                "item_id": item_id,
                "target_price": float(alert.target_price),
                "current_price": float(item.selling_price),
                "is_active": alert.is_active,
                "message": "Price alert created successfully"
            }
    
    async def cancel_price_alert(
        self,
        user_id: int,
        item_id: int
    ) -> bool:
        """
        Cancel price alert for an item
        
        Args:
            user_id: User ID
            item_id: Item ID
        
        Returns:
            bool: True if cancelled, False if not found
        """
        from app.repositories.secondhand import PriceAlertRepository
        
        alert_repo = PriceAlertRepository(self.item_repo.session)
        deleted = await alert_repo.delete(user_id, item_id)
        
        if deleted:
            logger.info(
                "Price alert cancelled",
                user_id=user_id,
                item_id=item_id
            )
        
        return deleted
    
    async def get_user_price_alerts(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[dict], int]:
        """
        Get user's price alerts with item information
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of alerts per page
        
        Returns:
            Tuple of (list of alert dicts, total count)
        """
        from app.repositories.secondhand import PriceAlertRepository
        
        alert_repo = PriceAlertRepository(self.item_repo.session)
        
        offset = (page - 1) * page_size
        alerts = await alert_repo.list_by_user(
            user_id=user_id,
            offset=offset,
            limit=page_size
        )
        
        # Get items and build response
        alert_list = []
        for alert in alerts:
            item = await self.item_repo.get_by_id(alert.item_id)
            if item:
                alert_list.append({
                    "alert_id": alert.id,
                    "item_id": alert.item_id,
                    "item_title": item.title,
                    "item_status": item.status.value,
                    "current_price": float(item.selling_price),
                    "target_price": float(alert.target_price),
                    "is_active": alert.is_active,
                    "is_triggered": float(item.selling_price) <= float(alert.target_price),
                    "notified_at": alert.notified_at.isoformat() if alert.notified_at else None,
                    "created_at": alert.created_at.isoformat()
                })
        
        # Get total count
        total = await alert_repo.count_by_user(user_id)
        
        logger.info(
            "Listed user price alerts",
            user_id=user_id,
            page=page,
            page_size=page_size,
            count=len(alert_list)
        )
        
        return alert_list, total
    
    async def check_and_trigger_price_alerts(self, item_id: int) -> int:
        """
        Check if item price has dropped below any alert thresholds
        and trigger notifications
        
        This should be called when an item's price is updated
        
        Args:
            item_id: Item ID
        
        Returns:
            int: Number of alerts triggered
        """
        from app.repositories.secondhand import PriceAlertRepository
        from datetime import datetime
        
        # Get item
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            return 0
        
        # Get active alerts for this item
        alert_repo = PriceAlertRepository(self.item_repo.session)
        alerts = await alert_repo.list_active_by_item(item_id)
        
        triggered_count = 0
        for alert in alerts:
            # Check if price dropped below target
            if item.selling_price <= alert.target_price:
                # Mark as notified
                alert.notified_at = datetime.utcnow()
                alert.is_active = False  # Deactivate after notification
                await alert_repo.update(alert)
                
                # TODO: Send notification to user
                # This would integrate with notification service
                
                triggered_count += 1
                
                logger.info(
                    "Price alert triggered",
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    item_id=item_id,
                    target_price=float(alert.target_price),
                    current_price=float(item.selling_price)
                )
        
        return triggered_count


class SecondhandOrderService:
    """Service for secondhand order operations"""
    
    def __init__(
        self,
        order_repository: SecondhandOrderRepository,
        item_repository: SecondhandItemRepository,
    ):
        self.order_repo = order_repository
        self.item_repo = item_repository
    
    async def create_order(
        self,
        buyer_id: int,
        item_id: int,
        school_id: int,
        delivery_method: str,
        delivery_address: Optional[str] = None,
        buyer_note: Optional[str] = None,
    ) -> SecondhandOrder:
        """
        Create a new order (buyer initiates purchase)
        
        Args:
            buyer_id: Buyer user ID
            item_id: Item ID
            school_id: School ID
            delivery_method: Delivery method (face_to_face or express)
            delivery_address: Delivery address (required for express)
            buyer_note: Optional buyer note
        
        Returns:
            Created order
        
        Raises:
            ResourceNotFoundError: If item not found
            ValidationError: If validation fails
            PermissionDeniedError: If buyer is the seller
        """
        # Get item
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            raise ResourceNotFoundError(f"Item {item_id} not found")
        
        # Check if item is available
        if item.status != ItemStatus.ON_SALE:
            raise ValidationError("Item is not available for purchase")
        
        # Check if buyer is not the seller
        if item.seller_id == buyer_id:
            raise PermissionDeniedError("You cannot buy your own item")
        
        # Validate delivery method
        try:
            delivery_method_enum = DeliveryMethod(delivery_method)
        except ValueError:
            raise ValidationError(f"Invalid delivery method: {delivery_method}")
        
        # Validate delivery address for express
        if delivery_method_enum == DeliveryMethod.EXPRESS and not delivery_address:
            raise ValidationError("Delivery address is required for express delivery")
        
        # Check if order already exists for this buyer and item
        existing_order = await self.order_repo.get_by_item_and_buyer(item_id, buyer_id)
        if existing_order and existing_order.status not in [OrderStatus.CANCELLED, OrderStatus.COMPLETED]:
            raise ValidationError("You already have an active order for this item")
        
        # Create order
        order = SecondhandOrder(
            item_id=item_id,
            buyer_id=buyer_id,
            seller_id=item.seller_id,
            school_id=school_id,
            price=item.selling_price,
            delivery_method=delivery_method_enum,
            delivery_address=delivery_address,
            buyer_note=buyer_note,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID,
        )
        
        created_order = await self.order_repo.create(order)
        
        logger.info(
            "Order created",
            order_id=created_order.id,
            buyer_id=buyer_id,
            seller_id=item.seller_id,
            item_id=item_id,
            price=float(item.selling_price),
        )
        
        return created_order
    
    async def get_order(self, order_id: int, user_id: int) -> SecondhandOrder:
        """
        Get order by ID
        
        Args:
            order_id: Order ID
            user_id: User ID (must be buyer or seller)
        
        Returns:
            Order
        
        Raises:
            ResourceNotFoundError: If order not found
            PermissionDeniedError: If user is not buyer or seller
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found")
        
        # Check permission
        if order.buyer_id != user_id and order.seller_id != user_id:
            raise PermissionDeniedError("You can only view your own orders")
        
        return order
    
    async def confirm_order(self, order_id: int, seller_id: int) -> SecondhandOrder:
        """
        Confirm order (seller confirms)
        
        Args:
            order_id: Order ID
            seller_id: Seller ID (must be the seller)
        
        Returns:
            Updated order
        
        Raises:
            ResourceNotFoundError: If order not found
            PermissionDeniedError: If user is not the seller
            ValidationError: If order status is invalid
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found")
        
        # Check permission
        if order.seller_id != seller_id:
            raise PermissionDeniedError("Only the seller can confirm the order")
        
        # Check status
        if order.status != OrderStatus.PENDING:
            raise ValidationError(f"Cannot confirm order with status: {order.status.value}")
        
        # Update status
        order.status = OrderStatus.CONFIRMED
        updated_order = await self.order_repo.update(order)
        
        logger.info(
            "Order confirmed by seller",
            order_id=order_id,
            seller_id=seller_id,
        )
        
        return updated_order
    
    async def complete_order(self, order_id: int, buyer_id: int) -> SecondhandOrder:
        """
        Complete order (buyer confirms receipt)
        
        Args:
            order_id: Order ID
            buyer_id: Buyer ID (must be the buyer)
        
        Returns:
            Updated order
        
        Raises:
            ResourceNotFoundError: If order not found
            PermissionDeniedError: If user is not the buyer
            ValidationError: If order status is invalid
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found")
        
        # Check permission
        if order.buyer_id != buyer_id:
            raise PermissionDeniedError("Only the buyer can complete the order")
        
        # Check status
        if order.status != OrderStatus.CONFIRMED:
            raise ValidationError(f"Cannot complete order with status: {order.status.value}")
        
        # Update order status
        order.status = OrderStatus.COMPLETED
        updated_order = await self.order_repo.update(order)
        
        # Update item status to sold
        item = await self.item_repo.get_by_id(order.item_id)
        if item:
            item.status = ItemStatus.SOLD
            await self.item_repo.update(item)
        
        logger.info(
            "Order completed by buyer",
            order_id=order_id,
            buyer_id=buyer_id,
            item_id=order.item_id,
        )
        
        return updated_order
    
    async def cancel_order(
        self,
        order_id: int,
        user_id: int,
        cancel_reason: Optional[str] = None,
    ) -> SecondhandOrder:
        """
        Cancel order (buyer or seller can cancel)
        
        Args:
            order_id: Order ID
            user_id: User ID (must be buyer or seller)
            cancel_reason: Optional cancellation reason
        
        Returns:
            Updated order
        
        Raises:
            ResourceNotFoundError: If order not found
            PermissionDeniedError: If user is not buyer or seller
            ValidationError: If order status is invalid
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found")
        
        # Check permission
        if order.buyer_id != user_id and order.seller_id != user_id:
            raise PermissionDeniedError("Only buyer or seller can cancel the order")
        
        # Check status
        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise ValidationError(f"Cannot cancel order with status: {order.status.value}")
        
        # Update status
        order.status = OrderStatus.CANCELLED
        if cancel_reason:
            if user_id == order.buyer_id:
                order.buyer_note = f"Cancelled: {cancel_reason}"
            else:
                order.seller_note = f"Cancelled: {cancel_reason}"
        
        updated_order = await self.order_repo.update(order)
        
        logger.info(
            "Order cancelled",
            order_id=order_id,
            user_id=user_id,
            reason=cancel_reason,
        )
        
        return updated_order
    
    async def list_buyer_orders(
        self,
        buyer_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[SecondhandOrder], int]:
        """
        List orders for buyer
        
        Args:
            buyer_id: Buyer ID
            page: Page number (1-indexed)
            page_size: Number of orders per page
        
        Returns:
            Tuple of (list of orders, total count)
        """
        offset = (page - 1) * page_size
        orders = await self.order_repo.list_by_buyer(
            buyer_id=buyer_id,
            offset=offset,
            limit=page_size,
        )
        
        # Get total count
        total = await self.order_repo.count_by_buyer(buyer_id)
        
        logger.info(
            "Listed buyer orders",
            buyer_id=buyer_id,
            page=page,
            page_size=page_size,
            count=len(orders),
        )
        
        return orders, total
    
    async def list_seller_orders(
        self,
        seller_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[SecondhandOrder], int]:
        """
        List orders for seller
        
        Args:
            seller_id: Seller ID
            page: Page number (1-indexed)
            page_size: Number of orders per page
        
        Returns:
            Tuple of (list of orders, total count)
        """
        offset = (page - 1) * page_size
        orders = await self.order_repo.list_by_seller(
            seller_id=seller_id,
            offset=offset,
            limit=page_size,
        )
        
        # Get total count
        total = await self.order_repo.count_by_seller(seller_id)
        
        logger.info(
            "Listed seller orders",
            seller_id=seller_id,
            page=page,
            page_size=page_size,
            count=len(orders),
        )
        
        return orders, total
    
    async def get_chat_entry(self, order_id: int, user_id: int) -> dict:
        """
        Get IM chat entry for order (placeholder for future IM integration)
        
        Args:
            order_id: Order ID
            user_id: User ID (must be buyer or seller)
        
        Returns:
            Chat entry information
        
        Raises:
            ResourceNotFoundError: If order not found
            PermissionDeniedError: If user is not buyer or seller
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise ResourceNotFoundError(f"Order {order_id} not found")
        
        # Check permission
        if order.buyer_id != user_id and order.seller_id != user_id:
            raise PermissionDeniedError("You can only access chat for your own orders")
        
        # Determine the other party
        other_party_id = order.seller_id if user_id == order.buyer_id else order.buyer_id
        
        # Placeholder response for future IM integration
        return {
            "order_id": order_id,
            "conversation_id": f"order_{order_id}",  # Placeholder
            "other_party_id": other_party_id,
            "message": "IM integration pending - this is a placeholder chat entry",
            "chat_url": f"/im/conversations/order_{order_id}",  # Placeholder URL
        }
        
        logger.info(
            "Chat entry accessed",
            order_id=order_id,
            user_id=user_id,
        )
