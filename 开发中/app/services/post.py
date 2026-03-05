"""
Post Service

Business logic for post publishing, management, and interactions.
"""
from typing import List, Optional, Dict
from datetime import datetime
from redis.asyncio import Redis

from app.repositories.post import PostRepository, InteractionRepository
from app.services.content_audit import ContentAuditEngine
from app.models.post import Post, Comment
from app.core.exceptions import (
    ValidationError,
    PermissionDeniedError,
    ResourceNotFoundError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class PostService:
    """Service for post operations"""
    
    def __init__(
        self,
        post_repository: PostRepository,
        audit_engine: ContentAuditEngine,
        interaction_repository: Optional[InteractionRepository] = None,
        redis: Optional[Redis] = None
    ):
        self.post_repo = post_repository
        self.audit_engine = audit_engine
        self.interaction_repo = interaction_repository
        self.redis = redis
        
        # Redis cache TTL (5 minutes)
        self.cache_ttl = 300
    
    async def create_post(
        self,
        user_id: int,
        school_id: int,
        circle_id: int,
        title: str,
        content: str,
        post_type: str,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        poll_options: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None,
        is_anonymous: bool = False,
        is_draft: bool = False
    ) -> Post:
        """
        Create a new post
        
        Args:
            user_id: Author user ID
            school_id: School ID
            circle_id: Circle ID
            title: Post title
            content: Post content
            post_type: Post type (text, image, video, poll, question)
            images: List of image URLs
            videos: List of video URLs
            poll_options: Poll options for poll type posts
            tags: Post tags
            is_anonymous: Whether to publish anonymously
            is_draft: Whether to save as draft
        
        Returns:
            Created post
        
        Raises:
            ValidationError: If validation fails
        """
        # Validate post type
        valid_types = ["text", "image", "video", "poll", "question"]
        if post_type not in valid_types:
            raise ValidationError(
                f"Invalid post type: {post_type}. Must be one of {valid_types}"
            )
        
        # Validate required fields based on type
        if post_type == "image" and not images:
            raise ValidationError("Image posts must include at least one image")
        
        if post_type == "video" and not videos:
            raise ValidationError("Video posts must include at least one video")
        
        if post_type == "poll" and not poll_options:
            raise ValidationError("Poll posts must include poll options")
        
        # Validate content length
        if len(title) > 200:
            raise ValidationError("Title cannot exceed 200 characters")
        
        if len(content) > 5000:
            raise ValidationError("Content cannot exceed 5000 characters")
        
        # Determine initial status
        if is_draft:
            status = "draft"
            audit_result = None
        else:
            # Audit content before publishing
            audit_result = await self._audit_post_content(
                title=title,
                content=content,
                images=images or []
            )
            
            if audit_result["action"] == "block":
                raise ValidationError(
                    f"Content contains sensitive words: {', '.join(audit_result['found_words'])}"
                )
            
            status = "approved" if audit_result["action"] == "approve" else "pending"
        
        # Prepare post data
        post_data = {
            "author_id": user_id,
            "school_id": school_id,
            "circle_id": circle_id,
            "title": title,
            "content": content,
            "type": post_type,
            "images": images or [],
            "videos": videos or [],
            "poll_options": poll_options or [],
            "tags": tags or [],
            "is_anonymous": is_anonymous,
            "status": status,
            "audit_result": audit_result
        }
        
        # Create post
        post = await self.post_repo.create_post(post_data)
        
        logger.info(
            "Post created",
            post_id=post.post_id,
            user_id=user_id,
            circle_id=circle_id,
            status=status,
            is_anonymous=is_anonymous
        )
        
        return post
    
    async def _audit_post_content(
        self,
        title: str,
        content: str,
        images: List[str]
    ) -> Dict:
        """
        Audit post content using content audit engine
        
        Args:
            title: Post title
            content: Post content
            images: Image URLs
        
        Returns:
            Audit result dictionary
        """
        # Combine title and content for text audit
        full_text = f"{title}\n{content}"
        
        # Audit content
        audit_result = await self.audit_engine.audit_content(
            text=full_text,
            images=images if images else None,
            strict_mode=False
        )
        
        return audit_result.to_dict()
    
    async def publish_draft(self, post_id: int, user_id: int) -> Post:
        """
        Publish a draft post
        
        Args:
            post_id: Post ID
            user_id: User ID (must be the author)
        
        Returns:
            Published post
        
        Raises:
            ResourceNotFoundError: If post not found
            PermissionDeniedError: If user is not the author
            ValidationError: If post is not a draft
        """
        # Get post
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Check permission
        if post.author_id != user_id:
            raise PermissionDeniedError("You can only publish your own drafts")
        
        # Check if draft
        if post.status != "draft":
            raise ValidationError("Only draft posts can be published")
        
        # Audit content
        audit_result = await self._audit_post_content(
            title=post.title,
            content=post.content,
            images=post.images
        )
        
        if audit_result["action"] == "block":
            raise ValidationError(
                f"Content contains sensitive words: {', '.join(audit_result['found_words'])}"
            )
        
        # Update status
        status = "approved" if audit_result["action"] == "approve" else "pending"
        updated_post = await self.post_repo.update_post_status(
            post_id=post_id,
            status=status,
            audit_result=audit_result
        )
        
        logger.info(
            "Draft published",
            post_id=post_id,
            user_id=user_id,
            status=status
        )
        
        return updated_post
    
    async def update_post(
        self,
        post_id: int,
        user_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Post:
        """
        Update a post
        
        Args:
            post_id: Post ID
            user_id: User ID (must be the author)
            title: New title
            content: New content
            images: New images
            videos: New videos
            tags: New tags
        
        Returns:
            Updated post
        
        Raises:
            ResourceNotFoundError: If post not found
            PermissionDeniedError: If user is not the author
        """
        # Get post
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Check permission
        if post.author_id != user_id:
            raise PermissionDeniedError("You can only update your own posts")
        
        # Prepare update data
        update_data = {}
        if title is not None:
            if len(title) > 200:
                raise ValidationError("Title cannot exceed 200 characters")
            update_data["title"] = title
        
        if content is not None:
            if len(content) > 5000:
                raise ValidationError("Content cannot exceed 5000 characters")
            update_data["content"] = content
        
        if images is not None:
            update_data["images"] = images
        
        if videos is not None:
            update_data["videos"] = videos
        
        if tags is not None:
            update_data["tags"] = tags
        
        # If content changed and post is published, re-audit
        if (title is not None or content is not None) and post.status == "approved":
            audit_result = await self._audit_post_content(
                title=title if title is not None else post.title,
                content=content if content is not None else post.content,
                images=images if images is not None else post.images
            )
            
            if audit_result["action"] == "block":
                raise ValidationError(
                    f"Content contains sensitive words: {', '.join(audit_result['found_words'])}"
                )
            
            update_data["status"] = "approved" if audit_result["action"] == "approve" else "pending"
            update_data["audit_result"] = audit_result
        
        # Update post
        updated_post = await self.post_repo.update_post(post_id, update_data)
        
        logger.info(
            "Post updated",
            post_id=post_id,
            user_id=user_id,
            fields=list(update_data.keys())
        )
        
        return updated_post
    
    async def delete_post(self, post_id: int, user_id: int) -> bool:
        """
        Delete a post
        
        Args:
            post_id: Post ID
            user_id: User ID (must be the author)
        
        Returns:
            True if deleted
        
        Raises:
            ResourceNotFoundError: If post not found
            PermissionDeniedError: If user is not the author
        """
        # Get post
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Check permission
        if post.author_id != user_id:
            raise PermissionDeniedError("You can only delete your own posts")
        
        # Delete post
        success = await self.post_repo.delete_post(post_id)
        
        if success:
            logger.info("Post deleted", post_id=post_id, user_id=user_id)
        
        return success
    
    async def get_post(self, post_id: int, user_id: Optional[int] = None) -> Post:
        """
        Get post by ID
        
        Args:
            post_id: Post ID
            user_id: Optional user ID for permission check
        
        Returns:
            Post
        
        Raises:
            ResourceNotFoundError: If post not found
        """
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Increment view count (async, don't wait)
        await self.post_repo.increment_view_count(post_id)
        
        return post
    
    async def list_circle_posts(
        self,
        circle_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "latest"
    ) -> tuple[List[Post], int]:
        """
        List posts in a circle with sorting
        
        Args:
            circle_id: Circle ID
            school_id: School ID (for data isolation)
            page: Page number (1-indexed)
            page_size: Number of posts per page
            sort_by: Sort method (latest, hot, featured)
        
        Returns:
            Tuple of (list of posts, total count)
        
        Raises:
            ValidationError: If sort_by is invalid
        """
        # Validate sort_by parameter
        valid_sorts = ["latest", "hot", "featured"]
        if sort_by not in valid_sorts:
            raise ValidationError(
                f"Invalid sort_by: {sort_by}. Must be one of {valid_sorts}"
            )
        
        skip = (page - 1) * page_size
        
        # Get posts with sorting
        posts = await self.post_repo.list_posts_by_circle(
            circle_id=circle_id,
            school_id=school_id,
            skip=skip,
            limit=page_size,
            status="approved",
            sort_by=sort_by
        )
        
        # Get total count
        is_featured = True if sort_by == "featured" else None
        total = await self.post_repo.count_posts_by_circle(
            circle_id=circle_id,
            school_id=school_id,
            status="approved",
            is_featured=is_featured
        )
        
        logger.info(
            "Listed circle posts",
            circle_id=circle_id,
            school_id=school_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            count=len(posts),
            total=total
        )
        
        return posts, total
    
    async def list_user_posts(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[Post]:
        """
        List posts by user
        
        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Number of posts per page
        
        Returns:
            List of posts
        """
        skip = (page - 1) * page_size
        posts = await self.post_repo.list_posts_by_author(
            author_id=user_id,
            skip=skip,
            limit=page_size
        )
        return posts
    
    async def create_comment(
        self,
        post_id: int,
        user_id: int,
        content: str,
        parent_id: Optional[int] = None,
        reply_to_user_id: Optional[int] = None,
        is_anonymous: bool = False
    ) -> Comment:
        """
        Create a comment on a post
        
        Args:
            post_id: Post ID
            user_id: Commenter user ID
            content: Comment content
            parent_id: Parent comment ID (for nested comments)
            reply_to_user_id: User being replied to
            is_anonymous: Whether to comment anonymously
        
        Returns:
            Created comment
        
        Raises:
            ResourceNotFoundError: If post not found
            ValidationError: If validation fails
        """
        # Check if post exists
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Validate content length
        if len(content) > 500:
            raise ValidationError("Comment cannot exceed 500 characters")
        
        # Audit comment content
        audit_result = await self.audit_engine.audit_text(content)
        if audit_result.action == "block":
            raise ValidationError(
                f"Comment contains sensitive words: {', '.join(audit_result.found_words)}"
            )
        
        # Create comment
        comment_data = {
            "post_id": post_id,
            "author_id": user_id,
            "content": content,
            "parent_id": parent_id,
            "reply_to_user_id": reply_to_user_id,
            "is_anonymous": is_anonymous
        }
        
        comment = await self.post_repo.create_comment(comment_data)
        
        logger.info(
            "Comment created",
            comment_id=comment.comment_id,
            post_id=post_id,
            user_id=user_id
        )
        
        return comment
    
    async def list_post_comments(
        self,
        post_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> List[Comment]:
        """
        List comments for a post
        
        Args:
            post_id: Post ID
            page: Page number (1-indexed)
            page_size: Number of comments per page
        
        Returns:
            List of comments
        """
        skip = (page - 1) * page_size
        comments = await self.post_repo.list_comments_by_post(
            post_id=post_id,
            skip=skip,
            limit=page_size
        )
        return comments
    
    async def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """
        Delete a comment
        
        Args:
            comment_id: Comment ID
            user_id: User ID (must be the author)
        
        Returns:
            True if deleted
        
        Raises:
            ResourceNotFoundError: If comment not found
            PermissionDeniedError: If user is not the author
        """
        # Get comment
        comment = await self.post_repo.get_comment_by_id(comment_id)
        if not comment:
            raise ResourceNotFoundError(f"Comment {comment_id} not found")
        
        # Check permission
        if comment.author_id != user_id:
            raise PermissionDeniedError("You can only delete your own comments")
        
        # Delete comment
        success = await self.post_repo.delete_comment(comment_id)
        
        if success:
            logger.info("Comment deleted", comment_id=comment_id, user_id=user_id)
        
        return success

    
    # ==================== Interaction Methods ====================
    
    async def _get_cached_count(self, cache_key: str) -> Optional[int]:
        """Get count from Redis cache"""
        if not self.redis:
            return None
        
        try:
            value = await self.redis.get(cache_key)
            return int(value) if value else None
        except Exception as e:
            logger.warning(f"Failed to get cached count: {e}")
            return None
    
    async def _set_cached_count(self, cache_key: str, count: int) -> None:
        """Set count in Redis cache"""
        if not self.redis:
            return
        
        try:
            await self.redis.setex(cache_key, self.cache_ttl, count)
        except Exception as e:
            logger.warning(f"Failed to set cached count: {e}")
    
    async def _invalidate_cache(self, post_id: int) -> None:
        """Invalidate all cached counts for a post"""
        if not self.redis:
            return
        
        try:
            keys = [
                f"post:{post_id}:like_count",
                f"post:{post_id}:comment_count",
                f"post:{post_id}:share_count",
                f"post:{post_id}:collect_count"
            ]
            await self.redis.delete(*keys)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
    
    async def like_post(self, post_id: int, user_id: int) -> Dict:
        """
        Like a post (toggle functionality)
        
        Args:
            post_id: Post ID
            user_id: User ID
        
        Returns:
            Dict with liked status and like count
        
        Raises:
            ResourceNotFoundError: If post not found
        """
        if not self.interaction_repo:
            raise RuntimeError("Interaction repository not initialized")
        
        # Check if post exists
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Check if already liked
        already_liked = await self.interaction_repo.check_interaction_exists(
            user_id=user_id,
            target_type="post",
            target_id=post_id,
            action_type="like"
        )
        
        if already_liked:
            # Unlike: remove interaction and decrement count
            await self.interaction_repo.delete_interaction(
                user_id=user_id,
                target_type="post",
                target_id=post_id,
                action_type="like"
            )
            await self.post_repo.increment_like_count(post_id, -1)
            liked = False
            logger.info("Post unliked", post_id=post_id, user_id=user_id)
        else:
            # Like: create interaction and increment count
            await self.interaction_repo.create_interaction(
                user_id=user_id,
                target_type="post",
                target_id=post_id,
                action_type="like"
            )
            await self.post_repo.increment_like_count(post_id, 1)
            liked = True
            logger.info("Post liked", post_id=post_id, user_id=user_id)
        
        # Get updated post
        updated_post = await self.post_repo.get_post_by_id(post_id)
        
        # Update cache
        cache_key = f"post:{post_id}:like_count"
        await self._set_cached_count(cache_key, updated_post.like_count)
        
        return {
            "liked": liked,
            "like_count": updated_post.like_count
        }
    
    async def collect_post(self, post_id: int, user_id: int) -> Dict:
        """
        Collect/bookmark a post (toggle functionality)
        
        Args:
            post_id: Post ID
            user_id: User ID
        
        Returns:
            Dict with collected status and collect count
        
        Raises:
            ResourceNotFoundError: If post not found
        """
        if not self.interaction_repo:
            raise RuntimeError("Interaction repository not initialized")
        
        # Check if post exists
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Check if already collected
        already_collected = await self.interaction_repo.check_interaction_exists(
            user_id=user_id,
            target_type="post",
            target_id=post_id,
            action_type="collect"
        )
        
        if already_collected:
            # Uncollect: remove interaction and decrement count
            await self.interaction_repo.delete_interaction(
                user_id=user_id,
                target_type="post",
                target_id=post_id,
                action_type="collect"
            )
            await self.post_repo.increment_collect_count(post_id, -1)
            collected = False
            logger.info("Post uncollected", post_id=post_id, user_id=user_id)
        else:
            # Collect: create interaction and increment count
            await self.interaction_repo.create_interaction(
                user_id=user_id,
                target_type="post",
                target_id=post_id,
                action_type="collect"
            )
            await self.post_repo.increment_collect_count(post_id, 1)
            collected = True
            logger.info("Post collected", post_id=post_id, user_id=user_id)
        
        # Get updated post
        updated_post = await self.post_repo.get_post_by_id(post_id)
        
        # Update cache
        cache_key = f"post:{post_id}:collect_count"
        await self._set_cached_count(cache_key, updated_post.collect_count)
        
        return {
            "collected": collected,
            "collect_count": updated_post.collect_count
        }
    
    async def share_post(self, post_id: int, user_id: int) -> Dict:
        """
        Share a post (increment share count)
        
        Args:
            post_id: Post ID
            user_id: User ID
        
        Returns:
            Dict with share count
        
        Raises:
            ResourceNotFoundError: If post not found
        """
        if not self.interaction_repo:
            raise RuntimeError("Interaction repository not initialized")
        
        # Check if post exists
        post = await self.post_repo.get_post_by_id(post_id)
        if not post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Create share interaction (can share multiple times)
        await self.interaction_repo.create_interaction(
            user_id=user_id,
            target_type="post",
            target_id=post_id,
            action_type="share"
        )
        
        # Increment share count
        await self.post_repo.increment_share_count(post_id)
        
        # Get updated post
        updated_post = await self.post_repo.get_post_by_id(post_id)
        
        # Update cache
        cache_key = f"post:{post_id}:share_count"
        await self._set_cached_count(cache_key, updated_post.share_count)
        
        logger.info("Post shared", post_id=post_id, user_id=user_id)
        
        return {
            "share_count": updated_post.share_count
        }
    
    async def forward_post(
        self,
        post_id: int,
        user_id: int,
        school_id: int,
        target_circle_id: int,
        forward_comment: Optional[str] = None
    ) -> Post:
        """
        Forward a post to another circle
        
        Args:
            post_id: Original post ID
            user_id: User ID forwarding the post
            school_id: School ID
            target_circle_id: Target circle ID
            forward_comment: Optional comment when forwarding
        
        Returns:
            New forwarded post
        
        Raises:
            ResourceNotFoundError: If original post not found
        """
        # Get original post
        original_post = await self.post_repo.get_post_by_id(post_id)
        if not original_post:
            raise ResourceNotFoundError(f"Post {post_id} not found")
        
        # Create forwarded post content
        forward_content = f"转发自帖子 #{post_id}"
        if forward_comment:
            forward_content = f"{forward_comment}\n\n{forward_content}"
        
        forward_content += f"\n\n原帖内容：\n{original_post.content}"
        
        # Create new post
        forwarded_post = await self.create_post(
            user_id=user_id,
            school_id=school_id,
            circle_id=target_circle_id,
            title=f"[转发] {original_post.title}",
            content=forward_content,
            post_type=original_post.type,
            images=original_post.images,
            videos=original_post.videos,
            tags=original_post.tags,
            is_anonymous=False,
            is_draft=False
        )
        
        # Increment original post's share count
        await self.post_repo.increment_share_count(post_id)
        
        # Update cache
        cache_key = f"post:{post_id}:share_count"
        updated_original = await self.post_repo.get_post_by_id(post_id)
        await self._set_cached_count(cache_key, updated_original.share_count)
        
        logger.info(
            "Post forwarded",
            original_post_id=post_id,
            new_post_id=forwarded_post.post_id,
            user_id=user_id,
            target_circle_id=target_circle_id
        )
        
        return forwarded_post
    
    async def get_user_liked_posts(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[int]:
        """
        Get list of post IDs that user has liked
        
        Args:
            user_id: User ID
            page: Page number
            page_size: Page size
        
        Returns:
            List of post IDs
        """
        if not self.interaction_repo:
            return []
        
        skip = (page - 1) * page_size
        interactions = await self.interaction_repo.get_user_interactions(
            user_id=user_id,
            target_type="post",
            action_type="like",
            skip=skip,
            limit=page_size
        )
        
        return [interaction["target_id"] for interaction in interactions]
    
    async def get_user_collected_posts(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> List[int]:
        """
        Get list of post IDs that user has collected
        
        Args:
            user_id: User ID
            page: Page number
            page_size: Page size
        
        Returns:
            List of post IDs
        """
        if not self.interaction_repo:
            return []
        
        skip = (page - 1) * page_size
        interactions = await self.interaction_repo.get_user_interactions(
            user_id=user_id,
            target_type="post",
            action_type="collect",
            skip=skip,
            limit=page_size
        )
        
        return [interaction["target_id"] for interaction in interactions]
    
    async def check_user_interactions(
        self,
        user_id: int,
        post_id: int
    ) -> Dict[str, bool]:
        """
        Check user's interactions with a post
        
        Args:
            user_id: User ID
            post_id: Post ID
        
        Returns:
            Dict with liked and collected status
        """
        if not self.interaction_repo:
            return {"liked": False, "collected": False}
        
        liked = await self.interaction_repo.check_interaction_exists(
            user_id=user_id,
            target_type="post",
            target_id=post_id,
            action_type="like"
        )
        
        collected = await self.interaction_repo.check_interaction_exists(
            user_id=user_id,
            target_type="post",
            target_id=post_id,
            action_type="collect"
        )
        
        return {
            "liked": liked,
            "collected": collected
        }


    # ==================== Recommendation Methods ====================
    
    async def get_personalized_recommendations(
        self,
        user_id: int,
        school_id: int,
        user_tags: Optional[List[str]],
        user_campus: Optional[str],
        user_major: Optional[str],
        page: int = 1,
        page_size: int = 20,
        exclude_viewed: bool = True
    ) -> tuple[List[Post], Dict]:
        """
        Get personalized content recommendations for user
        
        Algorithm:
        1. Get user's interest tags from profile
        2. Query posts matching user's tags (tag intersection)
        3. Boost posts from same school/campus/major (location bonus)
        4. Apply hot score for recency and engagement
        5. Combine scores: final_score = tag_match_score * 0.4 + hot_score * 0.3 + location_score * 0.3
        6. Return top N posts sorted by final_score
        
        Args:
            user_id: User ID
            school_id: School ID for data isolation
            user_tags: User's interest tags from profile
            user_campus: User's campus
            user_major: User's major
            page: Page number
            page_size: Number of posts per page
            exclude_viewed: Whether to exclude recently viewed posts
        
        Returns:
            Tuple of (list of posts, metadata dict with scoring info)
        """
        from app.repositories.post import RecommendationRepository
        
        # Initialize recommendation repository
        # Note: We need to get MongoDB database instance
        # For now, we'll use the post_repo's db
        if not hasattr(self.post_repo, 'db'):
            raise RuntimeError("Post repository does not have database instance")
        
        rec_repo = RecommendationRepository(self.post_repo.db)
        
        # Get excluded post IDs if needed
        exclude_post_ids = []
        if exclude_viewed:
            exclude_post_ids = await rec_repo.get_user_viewed_posts(user_id, days=7)
        
        # Fetch candidate posts from different sources
        tag_matched_posts = []
        hot_posts = []
        location_posts = []
        
        # 1. Get posts matching user's tags
        if user_tags:
            tag_matched_posts = await rec_repo.get_posts_by_tags(
                school_id=school_id,
                tags=user_tags,
                exclude_post_ids=exclude_post_ids,
                limit=50
            )
        
        # 2. Get hot posts
        hot_posts = await rec_repo.get_hot_posts(
            school_id=school_id,
            exclude_post_ids=exclude_post_ids,
            limit=50
        )
        
        # 3. Get posts from same location (campus/major)
        location_posts = await rec_repo.get_posts_by_location(
            school_id=school_id,
            campus=user_campus,
            major=user_major,
            exclude_post_ids=exclude_post_ids,
            limit=50
        )
        
        # Combine all posts and remove duplicates
        all_posts_dict = {}
        for post in tag_matched_posts + hot_posts + location_posts:
            if post.post_id not in all_posts_dict:
                all_posts_dict[post.post_id] = post
        
        all_posts = list(all_posts_dict.values())
        
        # If no posts found, return empty list
        if not all_posts:
            return [], {"algorithm": "hybrid", "total_candidates": 0}
        
        # Calculate scores for each post
        scored_posts = []
        for post in all_posts:
            # Calculate tag match score
            tag_score = self._calculate_tag_match_score(post, user_tags)
            
            # Calculate hot score
            hot_score = self._calculate_hot_score(post)
            
            # Calculate location score (requires author profile lookup)
            # For now, we'll use a simplified version based on school_id match
            location_score = self._calculate_location_score(
                post, school_id, user_campus, user_major
            )
            
            # Combine scores with weights
            # final_score = tag_match_score * 0.4 + hot_score * 0.3 + location_score * 0.3
            final_score = (tag_score * 0.4) + (hot_score * 0.3) + (location_score * 0.3)
            
            scored_posts.append({
                "post": post,
                "final_score": final_score,
                "tag_score": tag_score,
                "hot_score": hot_score,
                "location_score": location_score
            })
        
        # Sort by final score (descending)
        scored_posts.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_scored_posts = scored_posts[start_idx:end_idx]
        
        # Extract posts
        recommended_posts = [item["post"] for item in paginated_scored_posts]
        
        # Prepare metadata
        metadata = {
            "algorithm": "hybrid",
            "total_candidates": len(all_posts),
            "tag_matched_count": len(tag_matched_posts),
            "hot_posts_count": len(hot_posts),
            "location_posts_count": len(location_posts),
            "weights": {
                "tag_match": 0.4,
                "hot_score": 0.3,
                "location": 0.3
            }
        }
        
        logger.info(
            "Generated personalized recommendations",
            user_id=user_id,
            school_id=school_id,
            total_candidates=len(all_posts),
            recommended_count=len(recommended_posts),
            page=page
        )
        
        return recommended_posts, metadata
    
    def _calculate_tag_match_score(
        self,
        post: Post,
        user_tags: Optional[List[str]]
    ) -> float:
        """
        Calculate tag match score
        
        Score = (matching_tags / total_user_tags) * 100
        
        Args:
            post: Post to score
            user_tags: User's interest tags
        
        Returns:
            Tag match score (0-100)
        """
        if not user_tags or not post.tags:
            return 0.0
        
        # Calculate intersection
        matching_tags = set(post.tags) & set(user_tags)
        
        if not matching_tags:
            return 0.0
        
        # Calculate score
        score = (len(matching_tags) / len(user_tags)) * 100
        
        return min(score, 100.0)  # Cap at 100
    
    def _calculate_hot_score(self, post: Post) -> float:
        """
        Calculate hot score (normalized to 0-100)
        
        Hot score = (likes * 2 + comments * 3 + shares * 1.5) / (hours_since_creation + 2)^1.5
        
        Args:
            post: Post to score
        
        Returns:
            Hot score (0-100)
        """
        from datetime import datetime
        
        # Calculate engagement score
        engagement = (
            post.like_count * 2 +
            post.comment_count * 3 +
            post.share_count * 1.5
        )
        
        # Calculate hours since creation
        hours_since_creation = (datetime.now() - post.created_at).total_seconds() / 3600
        
        # Apply time decay formula
        time_factor = (hours_since_creation + 2) ** 1.5
        
        # Calculate hot score
        raw_hot_score = engagement / time_factor if time_factor > 0 else 0
        
        # Normalize to 0-100 scale (using log scale for better distribution)
        # Assuming max engagement score of ~1000 gives hot_score of ~10
        # We'll use a simple normalization: min(raw_score * 10, 100)
        normalized_score = min(raw_hot_score * 10, 100.0)
        
        return normalized_score
    
    def _calculate_location_score(
        self,
        post: Post,
        user_school_id: int,
        user_campus: Optional[str],
        user_major: Optional[str]
    ) -> float:
        """
        Calculate location score based on school/campus/major match
        
        Scoring:
        - Same school + same campus + same major: 100
        - Same school + same campus: 70
        - Same school: 40
        - Different school: 0
        
        Note: This is a simplified version. In production, you'd want to:
        1. Store author's campus/major in post document
        2. Or lookup author profile for each post (expensive)
        
        For now, we'll only check school_id match and return a base score.
        
        Args:
            post: Post to score
            user_school_id: User's school ID
            user_campus: User's campus
            user_major: User's major
        
        Returns:
            Location score (0-100)
        """
        # Check school match
        if post.school_id != user_school_id:
            return 0.0
        
        # Same school - base score of 40
        # TODO: In production, lookup author profile to check campus/major
        # For now, we'll return the base score
        return 40.0
    
    async def get_hot_posts_feed(
        self,
        school_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Post], int]:
        """
        Get hot posts feed across all circles
        
        Args:
            school_id: School ID for data isolation
            page: Page number
            page_size: Number of posts per page
        
        Returns:
            Tuple of (list of hot posts, total count)
        """
        from app.repositories.post import RecommendationRepository
        
        # Initialize recommendation repository
        if not hasattr(self.post_repo, 'db'):
            raise RuntimeError("Post repository does not have database instance")
        
        rec_repo = RecommendationRepository(self.post_repo.db)
        
        # Get hot posts
        hot_posts = await rec_repo.get_hot_posts(
            school_id=school_id,
            exclude_post_ids=None,
            limit=page_size * 3  # Fetch more for pagination
        )
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_posts = hot_posts[start_idx:end_idx]
        
        total = len(hot_posts)
        
        logger.info(
            "Retrieved hot posts feed",
            school_id=school_id,
            page=page,
            page_size=page_size,
            total=total
        )
        
        return paginated_posts, total
