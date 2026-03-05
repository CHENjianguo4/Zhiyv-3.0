"""
Post Schemas

Pydantic schemas for post API requests and responses.
"""
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ==================== Request Schemas ====================


class PollOptionCreate(BaseModel):
    """Poll option creation schema"""
    option: str = Field(..., min_length=1, max_length=100)


class PostCreate(BaseModel):
    """Post creation request schema"""
    circle_id: int = Field(..., gt=0, description="Circle ID")
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field(..., min_length=1, max_length=5000, description="Post content")
    type: str = Field(..., description="Post type: text, image, video, poll, question")
    images: Optional[List[str]] = Field(default=None, description="Image URLs")
    videos: Optional[List[str]] = Field(default=None, description="Video URLs")
    poll_options: Optional[List[PollOptionCreate]] = Field(default=None, description="Poll options")
    tags: Optional[List[str]] = Field(default=None, description="Post tags")
    is_anonymous: bool = Field(default=False, description="Publish anonymously")
    is_draft: bool = Field(default=False, description="Save as draft")
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        valid_types = ["text", "image", "video", "poll", "question"]
        if v not in valid_types:
            raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
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
    
    @field_validator("poll_options")
    @classmethod
    def validate_poll_options(cls, v):
        if v and len(v) < 2:
            raise ValueError("Poll must have at least 2 options")
        if v and len(v) > 10:
            raise ValueError("Poll cannot have more than 10 options")
        return v


class PostUpdate(BaseModel):
    """Post update request schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class CommentCreate(BaseModel):
    """Comment creation request schema"""
    content: str = Field(..., min_length=1, max_length=500, description="Comment content")
    parent_id: Optional[int] = Field(None, description="Parent comment ID for nested comments")
    reply_to_user_id: Optional[int] = Field(None, description="User being replied to")
    is_anonymous: bool = Field(default=False, description="Comment anonymously")


# ==================== Response Schemas ====================


class PollOptionResponse(BaseModel):
    """Poll option response schema"""
    option: str
    vote_count: int
    voters: List[int]


class AuditResultResponse(BaseModel):
    """Audit result response schema"""
    passed: bool
    reason: Optional[str] = None
    keywords: List[str] = []


class PostAuthorInfo(BaseModel):
    """Post author information (masked if anonymous)"""
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    is_anonymous: bool


class PostResponse(BaseModel):
    """Post response schema"""
    post_id: int
    circle_id: int
    author: PostAuthorInfo
    title: str
    content: str
    type: str
    images: List[str]
    videos: List[str]
    poll_options: List[PollOptionResponse]
    tags: List[str]
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    collect_count: int
    status: str
    is_pinned: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    """Post list response schema"""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
    sort_by: str = "latest"


class CommentAuthorInfo(BaseModel):
    """Comment author information (masked if anonymous)"""
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    is_anonymous: bool


class CommentResponse(BaseModel):
    """Comment response schema"""
    comment_id: int
    post_id: int
    author: CommentAuthorInfo
    content: str
    parent_id: Optional[int] = None
    reply_to_user_id: Optional[int] = None
    like_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Comment list response schema"""
    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int


# ==================== Helper Functions ====================


def post_to_response(post, author_info: Optional[Dict] = None) -> PostResponse:
    """
    Convert Post model to PostResponse
    
    Args:
        post: Post model instance
        author_info: Optional author information dict
    
    Returns:
        PostResponse
    """
    # Handle anonymous posts
    if post.is_anonymous:
        author = PostAuthorInfo(
            user_id=None,
            nickname="匿名用户",
            avatar=None,
            is_anonymous=True
        )
    else:
        author = PostAuthorInfo(
            user_id=post.author_id,
            nickname=author_info.get("nickname") if author_info else None,
            avatar=author_info.get("avatar") if author_info else None,
            is_anonymous=False
        )
    
    # Convert poll options
    poll_options = [
        PollOptionResponse(
            option=opt.option,
            vote_count=opt.vote_count,
            voters=opt.voters
        )
        for opt in post.poll_options
    ]
    
    return PostResponse(
        post_id=post.post_id,
        circle_id=post.circle_id,
        author=author,
        title=post.title,
        content=post.content,
        type=post.type,
        images=post.images,
        videos=post.videos,
        poll_options=poll_options,
        tags=post.tags,
        view_count=post.view_count,
        like_count=post.like_count,
        comment_count=post.comment_count,
        share_count=post.share_count,
        collect_count=post.collect_count,
        status=post.status,
        is_pinned=post.is_pinned,
        is_featured=post.is_featured,
        created_at=post.created_at,
        updated_at=post.updated_at
    )


def comment_to_response(comment, author_info: Optional[Dict] = None) -> CommentResponse:
    """
    Convert Comment model to CommentResponse
    
    Args:
        comment: Comment model instance
        author_info: Optional author information dict
    
    Returns:
        CommentResponse
    """
    # Handle anonymous comments
    if comment.is_anonymous:
        author = CommentAuthorInfo(
            user_id=None,
            nickname="匿名用户",
            avatar=None,
            is_anonymous=True
        )
    else:
        author = CommentAuthorInfo(
            user_id=comment.author_id,
            nickname=author_info.get("nickname") if author_info else None,
            avatar=author_info.get("avatar") if author_info else None,
            is_anonymous=False
        )
    
    return CommentResponse(
        comment_id=comment.comment_id,
        post_id=comment.post_id,
        author=author,
        content=comment.content,
        parent_id=comment.parent_id,
        reply_to_user_id=comment.reply_to_user_id,
        like_count=comment.like_count,
        created_at=comment.created_at
    )



# ==================== Interaction Schemas ====================


class LikeResponse(BaseModel):
    """Like response schema"""
    liked: bool
    like_count: int


class CollectResponse(BaseModel):
    """Collect response schema"""
    collected: bool
    collect_count: int


class ShareResponse(BaseModel):
    """Share response schema"""
    share_count: int


class ForwardPostRequest(BaseModel):
    """Forward post request schema"""
    target_circle_id: int = Field(..., gt=0, description="Target circle ID")
    forward_comment: Optional[str] = Field(None, max_length=500, description="Optional comment when forwarding")


class UserInteractionsResponse(BaseModel):
    """User interactions response schema"""
    liked: bool
    collected: bool



# ==================== Recommendation Schemas ====================


class RecommendationMetadata(BaseModel):
    """Recommendation metadata schema"""
    algorithm: str
    total_candidates: int
    tag_matched_count: Optional[int] = None
    hot_posts_count: Optional[int] = None
    location_posts_count: Optional[int] = None
    weights: Optional[Dict[str, float]] = None


class RecommendationResponse(BaseModel):
    """Recommendation response schema"""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
    metadata: RecommendationMetadata


class HotPostsResponse(BaseModel):
    """Hot posts response schema"""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
