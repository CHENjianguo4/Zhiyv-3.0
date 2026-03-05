"""
Post and Comment Models (MongoDB)

Defines document models for posts and comments stored in MongoDB.
"""
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2"""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ], serialization=core_schema.plain_serializer_function_ser_schema(str))

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class PollOption(BaseModel):
    """Poll option model"""
    option: str
    vote_count: int = 0
    voters: List[int] = Field(default_factory=list)


class AuditResult(BaseModel):
    """Audit result model"""
    passed: bool
    reason: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class Post(BaseModel):
    """Post document model for MongoDB"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    post_id: int  # Auto-increment ID
    school_id: int
    circle_id: int
    author_id: int
    title: str
    content: str
    type: str  # "text", "image", "video", "poll", "question"
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    poll_options: List[PollOption] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_anonymous: bool = False
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    collect_count: int = 0
    status: str = "pending"  # "pending", "approved", "rejected", "deleted"
    audit_result: Optional[AuditResult] = None
    is_pinned: bool = False
    is_featured: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Comment(BaseModel):
    """Comment document model for MongoDB"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    comment_id: int  # Auto-increment ID
    post_id: int
    author_id: int
    content: str
    parent_id: Optional[int] = None  # For nested comments
    reply_to_user_id: Optional[int] = None
    like_count: int = 0
    is_anonymous: bool = False
    status: str = "active"  # "active", "deleted"
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Interaction(BaseModel):
    """Interaction record (can be stored in MongoDB or MySQL)"""
    user_id: int
    target_type: str  # "post", "comment"
    target_id: int
    action_type: str  # "like", "collect", "share", "view"
    created_at: datetime = Field(default_factory=datetime.now)
