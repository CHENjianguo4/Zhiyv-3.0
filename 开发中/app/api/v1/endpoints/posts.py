"""
Posts API Endpoints

Handles post CRUD operations, publishing, and interactions.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_mysql_session, get_mongodb_database, get_redis
from app.core.dependencies import get_current_user
from app.core.permissions import require_verified
from app.core.response import success_response, error_response
from app.core.exceptions import ValidationError, PermissionDeniedError, ResourceNotFoundError
from app.repositories.post import PostRepository, InteractionRepository
from app.repositories.user import UserRepository
from app.services.post import PostService
from app.services.content_audit import ContentAuditEngine
from app.services.sensitive_word import SensitiveWordService
from app.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    CommentCreate,
    CommentResponse,
    CommentListResponse,
    LikeResponse,
    CollectResponse,
    ShareResponse,
    ForwardPostRequest,
    UserInteractionsResponse,
    RecommendationResponse,
    RecommendationMetadata,
    HotPostsResponse,
    post_to_response,
    comment_to_response
)
from app.models.user import User

router = APIRouter(prefix="/posts", tags=["posts"])


# ==================== Dependencies ====================


async def get_post_service(
    mongodb=Depends(get_mongodb_database),
    redis: Redis = Depends(get_redis)
) -> PostService:
    """Get post service instance"""
    post_repo = PostRepository(mongodb)
    interaction_repo = InteractionRepository(mongodb)
    sensitive_word_service = SensitiveWordService(redis)
    audit_engine = ContentAuditEngine(sensitive_word_service, redis)
    return PostService(post_repo, audit_engine, interaction_repo, redis)


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


# ==================== Post Endpoints ====================


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new post",
    description="Create a new post in a circle. Supports text, image, video, poll, and question types."
)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Create a new post
    
    - **circle_id**: Circle ID where the post will be published
    - **title**: Post title (max 200 characters)
    - **content**: Post content (max 5000 characters)
    - **type**: Post type (text, image, video, poll, question)
    - **images**: Optional list of image URLs (max 9)
    - **videos**: Optional list of video URLs (max 3)
    - **poll_options**: Optional poll options (for poll type, 2-10 options)
    - **tags**: Optional list of tags
    - **is_anonymous**: Whether to publish anonymously (default: false)
    - **is_draft**: Whether to save as draft (default: false)
    """
    try:
        # Convert poll options to dict format
        poll_options = None
        if post_data.poll_options:
            poll_options = [
                {"option": opt.option, "vote_count": 0, "voters": []}
                for opt in post_data.poll_options
            ]
        
        # Create post
        post = await post_service.create_post(
            user_id=current_user.id,
            school_id=current_user.school_id,
            circle_id=post_data.circle_id,
            title=post_data.title,
            content=post_data.content,
            post_type=post_data.type,
            images=post_data.images,
            videos=post_data.videos,
            poll_options=poll_options,
            tags=post_data.tags,
            is_anonymous=post_data.is_anonymous,
            is_draft=post_data.is_draft
        )
        
        # Get author info if not anonymous
        author_info = None
        if not post.is_anonymous:
            author_info = {
                "nickname": current_user.nickname,
                "avatar": current_user.avatar
            }
        
        return success_response(
            data=post_to_response(post, author_info),
            message="Post created successfully" if not post_data.is_draft else "Draft saved successfully"
        )
    
    except ValidationError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message=f"Failed to create post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    summary="Get post by ID",
    description="Get detailed information about a specific post"
)
async def get_post(
    post_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get post by ID
    
    - **post_id**: Post ID
    """
    try:
        post = await post_service.get_post(
            post_id=post_id,
            user_id=current_user.id if current_user else None
        )
        
        # Get author info if not anonymous
        author_info = None
        if not post.is_anonymous:
            author = await user_repo.get_by_id(post.author_id)
            if author:
                author_info = {
                    "nickname": author.nickname,
                    "avatar": author.avatar
                }
        
        return success_response(data=post_to_response(post, author_info))
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message=f"Failed to get post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.put(
    "/{post_id}",
    response_model=PostResponse,
    summary="Update post",
    description="Update an existing post (only by author)"
)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Update post
    
    - **post_id**: Post ID
    - **title**: Optional new title
    - **content**: Optional new content
    - **images**: Optional new images
    - **videos**: Optional new videos
    - **tags**: Optional new tags
    """
    try:
        post = await post_service.update_post(
            post_id=post_id,
            user_id=current_user.id,
            title=post_data.title,
            content=post_data.content,
            images=post_data.images,
            videos=post_data.videos,
            tags=post_data.tags
        )
        
        # Get author info
        author_info = {
            "nickname": current_user.nickname,
            "avatar": current_user.avatar
        }
        
        return success_response(
            data=post_to_response(post, author_info),
            message="Post updated successfully"
        )
    
    except (ResourceNotFoundError, PermissionDeniedError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN if isinstance(e, PermissionDeniedError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to update post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/{post_id}",
    summary="Delete post",
    description="Delete a post (only by author)"
)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Delete post
    
    - **post_id**: Post ID
    """
    try:
        await post_service.delete_post(post_id=post_id, user_id=current_user.id)
        return success_response(message="Post deleted successfully")
    
    except (ResourceNotFoundError, PermissionDeniedError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to delete post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{post_id}/publish",
    response_model=PostResponse,
    summary="Publish draft post",
    description="Publish a draft post"
)
async def publish_draft(
    post_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Publish a draft post
    
    - **post_id**: Post ID
    """
    try:
        post = await post_service.publish_draft(post_id=post_id, user_id=current_user.id)
        
        # Get author info
        author_info = {
            "nickname": current_user.nickname,
            "avatar": current_user.avatar
        }
        
        return success_response(
            data=post_to_response(post, author_info),
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
    "",
    response_model=PostListResponse,
    summary="List posts",
    description="List posts in a circle or by a user with sorting options"
)
async def list_posts(
    circle_id: Optional[int] = Query(None, description="Filter by circle ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    sort_by: str = Query("latest", description="Sort method: latest, hot, featured"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: Optional[User] = Depends(get_current_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    List posts with sorting options
    
    - **circle_id**: Optional circle ID to filter posts
    - **user_id**: Optional user ID to filter posts
    - **sort_by**: Sort method (latest, hot, featured) - default: latest
      - **latest**: Sort by created_at DESC (newest first)
      - **hot**: Sort by engagement score (likes + comments + shares weighted by recency)
      - **featured**: Filter by is_featured flag, then sort by created_at DESC
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    """
    try:
        # Get posts
        total = 0
        if circle_id:
            if not current_user:
                return error_response(
                    message="Authentication required",
                    code=status.HTTP_401_UNAUTHORIZED
                )
            posts, total = await post_service.list_circle_posts(
                circle_id=circle_id,
                school_id=current_user.school_id,
                page=page,
                page_size=page_size,
                sort_by=sort_by
            )
        elif user_id:
            posts = await post_service.list_user_posts(
                user_id=user_id,
                page=page,
                page_size=page_size
            )
            total = len(posts)  # TODO: Add total count for user posts
        else:
            return error_response(
                message="Either circle_id or user_id must be provided",
                code=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert to response format
        post_responses = []
        for post in posts:
            author_info = None
            if not post.is_anonymous:
                author = await user_repo.get_by_id(post.author_id)
                if author:
                    author_info = {
                        "nickname": author.nickname,
                        "avatar": author.avatar
                    }
            post_responses.append(post_to_response(post, author_info))
        
        return success_response(
            data=PostListResponse(
                posts=post_responses,
                total=total,
                page=page,
                page_size=page_size,
                sort_by=sort_by if circle_id else "latest"
            )
        )
    
    except ValidationError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message=f"Failed to list posts: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==================== Comment Endpoints ====================


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a comment",
    description="Create a comment on a post"
)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Create a comment
    
    - **post_id**: Post ID
    - **content**: Comment content (max 500 characters)
    - **parent_id**: Optional parent comment ID for nested comments
    - **reply_to_user_id**: Optional user ID being replied to
    - **is_anonymous**: Whether to comment anonymously (default: false)
    """
    try:
        comment = await post_service.create_comment(
            post_id=post_id,
            user_id=current_user.id,
            content=comment_data.content,
            parent_id=comment_data.parent_id,
            reply_to_user_id=comment_data.reply_to_user_id,
            is_anonymous=comment_data.is_anonymous
        )
        
        # Get author info if not anonymous
        author_info = None
        if not comment.is_anonymous:
            author_info = {
                "nickname": current_user.nickname,
                "avatar": current_user.avatar
            }
        
        return success_response(
            data=comment_to_response(comment, author_info),
            message="Comment created successfully"
        )
    
    except (ResourceNotFoundError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_400_BAD_REQUEST
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to create comment: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{post_id}/comments",
    response_model=CommentListResponse,
    summary="List comments",
    description="List comments for a post"
)
async def list_comments(
    post_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    List comments for a post
    
    - **post_id**: Post ID
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 50, max: 100)
    """
    try:
        comments = await post_service.list_post_comments(
            post_id=post_id,
            page=page,
            page_size=page_size
        )
        
        # Convert to response format
        comment_responses = []
        for comment in comments:
            author_info = None
            if not comment.is_anonymous:
                author = await user_repo.get_by_id(comment.author_id)
                if author:
                    author_info = {
                        "nickname": author.nickname,
                        "avatar": author.avatar
                    }
            comment_responses.append(comment_to_response(comment, author_info))
        
        return success_response(
            data=CommentListResponse(
                comments=comment_responses,
                total=len(comment_responses),  # TODO: Add total count query
                page=page,
                page_size=page_size
            )
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to list comments: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/{post_id}/comments/{comment_id}",
    summary="Delete comment",
    description="Delete a comment (only by author)"
)
async def delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Delete comment
    
    - **post_id**: Post ID
    - **comment_id**: Comment ID
    """
    try:
        await post_service.delete_comment(comment_id=comment_id, user_id=current_user.id)
        return success_response(message="Comment deleted successfully")
    
    except (ResourceNotFoundError, PermissionDeniedError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, ResourceNotFoundError) else \
               status.HTTP_403_FORBIDDEN
        return error_response(message=str(e), code=code)
    except Exception as e:
        return error_response(
            message=f"Failed to delete comment: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# ==================== Interaction Endpoints ====================


@router.post(
    "/{post_id}/like",
    response_model=LikeResponse,
    summary="Like/Unlike a post",
    description="Toggle like status for a post"
)
async def like_post(
    post_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Like or unlike a post (toggle functionality)
    
    - **post_id**: Post ID
    
    Returns the new like status and updated like count.
    """
    try:
        result = await post_service.like_post(post_id=post_id, user_id=current_user.id)
        
        message = "Post liked successfully" if result["liked"] else "Post unliked successfully"
        return success_response(data=result, message=message)
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message=f"Failed to like post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/{post_id}/like",
    response_model=LikeResponse,
    summary="Unlike a post",
    description="Remove like from a post (same as POST with toggle)"
)
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Unlike a post (convenience endpoint, same as POST /like)
    
    - **post_id**: Post ID
    """
    try:
        result = await post_service.like_post(post_id=post_id, user_id=current_user.id)
        
        return success_response(
            data=result,
            message="Post unliked successfully" if not result["liked"] else "Post liked successfully"
        )
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message=f"Failed to unlike post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{post_id}/collect",
    response_model=CollectResponse,
    summary="Collect/Uncollect a post",
    description="Toggle collect/bookmark status for a post"
)
async def collect_post(
    post_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Collect or uncollect a post (toggle functionality)
    
    - **post_id**: Post ID
    
    Returns the new collect status and updated collect count.
    """
    try:
        result = await post_service.collect_post(post_id=post_id, user_id=current_user.id)
        
        message = "Post collected successfully" if result["collected"] else "Post uncollected successfully"
        return success_response(data=result, message=message)
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message=f"Failed to collect post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.delete(
    "/{post_id}/collect",
    response_model=CollectResponse,
    summary="Uncollect a post",
    description="Remove post from collection (same as POST with toggle)"
)
async def uncollect_post(
    post_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Uncollect a post (convenience endpoint, same as POST /collect)
    
    - **post_id**: Post ID
    """
    try:
        result = await post_service.collect_post(post_id=post_id, user_id=current_user.id)
        
        return success_response(
            data=result,
            message="Post uncollected successfully" if not result["collected"] else "Post collected successfully"
        )
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message=f"Failed to uncollect post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{post_id}/share",
    response_model=ShareResponse,
    summary="Share a post",
    description="Increment share count for a post"
)
async def share_post(
    post_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Share a post (increments share count)
    
    - **post_id**: Post ID
    
    Returns the updated share count.
    """
    try:
        result = await post_service.share_post(post_id=post_id, user_id=current_user.id)
        
        return success_response(data=result, message="Post shared successfully")
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return error_response(
            message=f"Failed to share post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post(
    "/{post_id}/forward",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Forward a post to another circle",
    description="Create a forwarded post in another circle"
)
async def forward_post(
    post_id: int,
    forward_data: ForwardPostRequest,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Forward a post to another circle
    
    - **post_id**: Original post ID
    - **target_circle_id**: Target circle ID to forward to
    - **forward_comment**: Optional comment when forwarding
    
    Creates a new post in the target circle with reference to the original post.
    """
    try:
        forwarded_post = await post_service.forward_post(
            post_id=post_id,
            user_id=current_user.id,
            school_id=current_user.school_id,
            target_circle_id=forward_data.target_circle_id,
            forward_comment=forward_data.forward_comment
        )
        
        # Get author info
        author_info = {
            "nickname": current_user.nickname,
            "avatar": current_user.avatar
        }
        
        return success_response(
            data=post_to_response(forwarded_post, author_info),
            message="Post forwarded successfully"
        )
    
    except ResourceNotFoundError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_404_NOT_FOUND
        )
    except ValidationError as e:
        return error_response(
            message=str(e),
            code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message=f"Failed to forward post: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/{post_id}/interactions",
    response_model=UserInteractionsResponse,
    summary="Get user's interactions with a post",
    description="Check if current user has liked or collected the post"
)
async def get_user_interactions(
    post_id: int,
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service)
):
    """
    Get user's interactions with a post
    
    - **post_id**: Post ID
    
    Returns whether the user has liked and/or collected the post.
    """
    try:
        result = await post_service.check_user_interactions(
            user_id=current_user.id,
            post_id=post_id
        )
        
        return success_response(data=result)
    
    except Exception as e:
        return error_response(
            message=f"Failed to get user interactions: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# ==================== Recommendation Endpoints ====================


@router.get(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Get personalized recommendations",
    description="Get personalized content recommendations based on user's interests, location, and engagement"
)
async def get_recommendations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    exclude_viewed: bool = Query(True, description="Exclude recently viewed posts"),
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get personalized content recommendations
    
    This endpoint uses a hybrid recommendation algorithm that combines:
    - **Tag matching**: Posts matching user's interest tags (40% weight)
    - **Hot score**: Posts with high engagement and recency (30% weight)
    - **Location**: Posts from same campus/major (30% weight)
    
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    - **exclude_viewed**: Exclude recently viewed posts (default: true)
    
    Returns a personalized feed of posts sorted by combined score.
    """
    try:
        # Get user profile for tags and location
        user_profile = await user_repo.get_profile(current_user.id)
        
        # Extract tags from profile
        user_tags = None
        if user_profile and user_profile.tags:
            # Tags are stored as JSON, could be list or dict
            if isinstance(user_profile.tags, list):
                user_tags = user_profile.tags
            elif isinstance(user_profile.tags, dict):
                # If tags is a dict, extract values or keys depending on structure
                user_tags = list(user_profile.tags.keys()) if user_profile.tags else None
        
        # Get campus and major
        user_campus = user_profile.campus if user_profile else None
        user_major = user_profile.major if user_profile else None
        
        # Get recommendations
        posts, metadata = await post_service.get_personalized_recommendations(
            user_id=current_user.id,
            school_id=current_user.school_id,
            user_tags=user_tags,
            user_campus=user_campus,
            user_major=user_major,
            page=page,
            page_size=page_size,
            exclude_viewed=exclude_viewed
        )
        
        # Convert to response format
        post_responses = []
        for post in posts:
            author_info = None
            if not post.is_anonymous:
                author = await user_repo.get_by_id(post.author_id)
                if author:
                    author_info = {
                        "nickname": author.nickname,
                        "avatar": author.avatar
                    }
            post_responses.append(post_to_response(post, author_info))
        
        return success_response(
            data=RecommendationResponse(
                posts=post_responses,
                total=metadata.get("total_candidates", 0),
                page=page,
                page_size=page_size,
                metadata=RecommendationMetadata(**metadata)
            )
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to get recommendations: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get(
    "/hot",
    response_model=HotPostsResponse,
    summary="Get hot posts",
    description="Get hot posts across all circles based on engagement and recency"
)
async def get_hot_posts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_verified_user),
    post_service: PostService = Depends(get_post_service),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get hot posts feed
    
    Returns posts sorted by hot score algorithm:
    - Hot score = (likes * 2 + comments * 3 + shares * 1.5) / (hours_since_creation + 2)^1.5
    
    - **page**: Page number (default: 1)
    - **page_size**: Page size (default: 20, max: 100)
    
    Returns a feed of hot posts from the last 7 days.
    """
    try:
        # Get hot posts
        posts, total = await post_service.get_hot_posts_feed(
            school_id=current_user.school_id,
            page=page,
            page_size=page_size
        )
        
        # Convert to response format
        post_responses = []
        for post in posts:
            author_info = None
            if not post.is_anonymous:
                author = await user_repo.get_by_id(post.author_id)
                if author:
                    author_info = {
                        "nickname": author.nickname,
                        "avatar": author.avatar
                    }
            post_responses.append(post_to_response(post, author_info))
        
        return success_response(
            data=HotPostsResponse(
                posts=post_responses,
                total=total,
                page=page,
                page_size=page_size
            )
        )
    
    except Exception as e:
        return error_response(
            message=f"Failed to get hot posts: {str(e)}",
            code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
