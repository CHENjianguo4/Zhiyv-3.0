"""
Secondhand Item Schemas

Pydantic schemas for secondhand item API requests and responses.
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


# ==================== Request Schemas ====================


class ItemCreate(BaseModel):
    """Item creation request schema"""
    title: str = Field(..., min_length=1, max_length=200, description="Item title")
    description: Optional[str] = Field(None, description="Item description")
    category: str = Field(..., description="Item category")
    condition: str = Field(..., description="Item condition")
    selling_price: Decimal = Field(..., gt=0, description="Selling price")
    original_price: Optional[Decimal] = Field(None, description="Original price")
    images: Optional[List[str]] = Field(default=None, description="Image URLs")
    videos: Optional[List[str]] = Field(default=None, description="Video URLs")
    location: Optional[str] = Field(None, description="Trading location")
    is_negotiable: bool = Field(default=False, description="Whether price is negotiable")
    delivery_method: str = Field(..., description="Delivery method")
    is_draft: bool = Field(default=False, description="Save as draft")
    
    @field_validator("category")
    @classmethod
    def validate_category(cls, v):
        valid_categories = ["electronics", "textbook", "daily", "sports", "other"]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")
        return v
    
    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v):
        valid_conditions = ["brand_new", "like_new", "lightly_used", "well_used", "heavily_used"]
        if v not in valid_conditions:
            raise ValueError(f"Condition must be one of: {', '.join(valid_conditions)}")
        return v
    
    @field_validator("delivery_method")
    @classmethod
    def validate_delivery_method(cls, v):
        valid_methods = ["face_to_face", "express", "both"]
        if v not in valid_methods:
            raise ValueError(f"Delivery method must be one of: {', '.join(valid_methods)}")
        return v
    
    @field_validator("images")
    @classmethod
    def validate_images(cls, v):
        if v and len(v) > 9:
            raise ValueError("Maximum 9 images allowed")
        return v
    
    @field_validator("videos")
    @classmethod
    def validate_videos(cls, v):
        if v and len(v) > 3:
            raise ValueError("Maximum 3 videos allowed")
        return v
    
    @field_validator("original_price")
    @classmethod
    def validate_original_price(cls, v, info):
        if v is not None and "selling_price" in info.data:
            if v < info.data["selling_price"]:
                raise ValueError("Original price cannot be less than selling price")
        return v


class ItemUpdate(BaseModel):
    """Item update request schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    selling_price: Optional[Decimal] = Field(None, gt=0)
    original_price: Optional[Decimal] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    location: Optional[str] = None
    is_negotiable: Optional[bool] = None
    delivery_method: Optional[str] = None
    
    @field_validator("delivery_method")
    @classmethod
    def validate_delivery_method(cls, v):
        if v is not None:
            valid_methods = ["face_to_face", "express", "both"]
            if v not in valid_methods:
                raise ValueError(f"Delivery method must be one of: {', '.join(valid_methods)}")
        return v


class UploadRequest(BaseModel):
    """File upload request schema (placeholder)"""
    file_type: str = Field(..., description="File type: image or video")
    
    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v):
        valid_types = ["image", "video"]
        if v not in valid_types:
            raise ValueError(f"File type must be one of: {', '.join(valid_types)}")
        return v


# ==================== Response Schemas ====================


class SellerInfo(BaseModel):
    """Seller information"""
    user_id: int
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    credit_score: Optional[int] = None


class ItemResponse(BaseModel):
    """Item response schema"""
    id: int
    seller: SellerInfo
    title: str
    description: Optional[str] = None
    category: str
    condition: str
    selling_price: Decimal
    original_price: Optional[Decimal] = None
    images: List[str]
    videos: List[str]
    location: Optional[str] = None
    is_negotiable: bool
    delivery_method: str
    status: str
    view_count: int
    favorite_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """Item list response schema"""
    items: List[ItemResponse]
    total: int
    page: int
    page_size: int


class UploadResponse(BaseModel):
    """File upload response schema (placeholder)"""
    url: str
    file_type: str
    file_size: Optional[int] = None


# ==================== Helper Functions ====================


def item_to_response(item, seller_info: Optional[dict] = None) -> ItemResponse:
    """
    Convert SecondhandItem model to ItemResponse
    
    Args:
        item: SecondhandItem model instance
        seller_info: Optional seller information dict
    
    Returns:
        ItemResponse
    """
    seller = SellerInfo(
        user_id=item.seller_id,
        nickname=seller_info.get("nickname") if seller_info else None,
        avatar=seller_info.get("avatar") if seller_info else None,
        credit_score=seller_info.get("credit_score") if seller_info else None
    )
    
    # Extract image and video URLs from JSON
    images = item.images.get("urls", []) if item.images else []
    videos = item.videos.get("urls", []) if item.videos else []
    
    return ItemResponse(
        id=item.id,
        seller=seller,
        title=item.title,
        description=item.description,
        category=item.category.value,
        condition=item.condition.value,
        selling_price=item.selling_price,
        original_price=item.original_price,
        images=images,
        videos=videos,
        location=item.location,
        is_negotiable=item.is_negotiable,
        delivery_method=item.delivery_method.value,
        status=item.status.value,
        view_count=item.view_count,
        favorite_count=item.favorite_count,
        created_at=item.created_at,
        updated_at=item.updated_at
    )


# ==================== Order Schemas ====================


class OrderCreate(BaseModel):
    """Order creation request schema"""
    item_id: int = Field(..., description="Item ID")
    delivery_method: str = Field(..., description="Delivery method (face_to_face or express)")
    delivery_address: Optional[str] = Field(None, description="Delivery address (required for express)")
    buyer_note: Optional[str] = Field(None, max_length=500, description="Buyer note")
    
    @field_validator("delivery_method")
    @classmethod
    def validate_delivery_method(cls, v):
        valid_methods = ["face_to_face", "express"]
        if v not in valid_methods:
            raise ValueError(f"Delivery method must be one of: {', '.join(valid_methods)}")
        return v


class OrderResponse(BaseModel):
    """Order response schema"""
    id: int
    item_id: int
    buyer_id: int
    seller_id: int
    price: Decimal
    delivery_method: str
    delivery_address: Optional[str] = None
    status: str
    payment_status: str
    buyer_note: Optional[str] = None
    seller_note: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list response schema"""
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


class OrderCancelRequest(BaseModel):
    """Order cancellation request schema"""
    cancel_reason: Optional[str] = Field(None, max_length=500, description="Cancellation reason")


class ChatEntryResponse(BaseModel):
    """Chat entry response schema (placeholder)"""
    order_id: int
    conversation_id: str
    other_party_id: int
    message: str
    chat_url: str


def order_to_response(order) -> OrderResponse:
    """
    Convert SecondhandOrder model to OrderResponse
    
    Args:
        order: SecondhandOrder model instance
    
    Returns:
        OrderResponse
    """
    return OrderResponse(
        id=order.id,
        item_id=order.item_id,
        buyer_id=order.buyer_id,
        seller_id=order.seller_id,
        price=order.price,
        delivery_method=order.delivery_method.value,
        delivery_address=order.delivery_address,
        status=order.status.value,
        payment_status=order.payment_status.value,
        buyer_note=order.buyer_note,
        seller_note=order.seller_note,
        completed_at=order.completed_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
