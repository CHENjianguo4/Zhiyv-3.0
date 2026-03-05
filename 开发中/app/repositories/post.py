"""
Post Repository

Handles MongoDB operations for posts and comments.
"""
from typing import List, Optional, Dict
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.post import Post, Comment, PollOption, AuditResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class PostRepository:
    """Repository for post operations in MongoDB"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.posts_collection = db["posts"]
        self.comments_collection = db["comments"]
        self.counters_collection = db["counters"]
    
    async def _get_next_post_id(self) -> int:
        """Get next auto-increment post ID"""
        result = await self.counters_collection.find_one_and_update(
            {"_id": "post_id"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        return result["seq"]
    
    async def _get_next_comment_id(self) -> int:
        """Get next auto-increment comment ID"""
        result = await self.counters_collection.find_one_and_update(
            {"_id": "comment_id"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        return result["seq"]
    
    async def create_post(self, post_data: Dict) -> Post:
        """
        Create a new post
        
        Args:
            post_data: Post data dictionary
        
        Returns:
            Created post
        """
        # Get next post ID
        post_id = await self._get_next_post_id()
        
        # Prepare post document
        post_doc = {
            "post_id": post_id,
            "school_id": post_data["school_id"],
            "circle_id": post_data["circle_id"],
            "author_id": post_data["author_id"],
            "title": post_data["title"],
            "content": post_data["content"],
            "type": post_data["type"],
            "images": post_data.get("images", []),
            "videos": post_data.get("videos", []),
            "poll_options": post_data.get("poll_options", []),
            "tags": post_data.get("tags", []),
            "is_anonymous": post_data.get("is_anonymous", False),
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0,
            "collect_count": 0,
            "status": post_data.get("status", "pending"),
            "audit_result": post_data.get("audit_result"),
            "is_pinned": False,
            "is_featured": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Insert into MongoDB
        result = await self.posts_collection.insert_one(post_doc)
        post_doc["_id"] = result.inserted_id
        
        logger.info(
            "Created post",
            post_id=post_id,
            author_id=post_data["author_id"],
            circle_id=post_data["circle_id"]
        )
        
        return Post(**post_doc)
    
    async def get_post_by_id(self, post_id: int) -> Optional[Post]:
        """
        Get post by ID
        
        Args:
            post_id: Post ID
        
        Returns:
            Post if found, None otherwise
        """
        post_doc = await self.posts_collection.find_one({"post_id": post_id})
        if post_doc:
            return Post(**post_doc)
        return None
    
    async def update_post(self, post_id: int, update_data: Dict) -> Optional[Post]:
        """
        Update post
        
        Args:
            post_id: Post ID
            update_data: Fields to update
        
        Returns:
            Updated post if found, None otherwise
        """
        update_data["updated_at"] = datetime.now()
        
        result = await self.posts_collection.find_one_and_update(
            {"post_id": post_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info("Updated post", post_id=post_id, fields=list(update_data.keys()))
            return Post(**result)
        return None
    
    async def update_post_status(
        self,
        post_id: int,
        status: str,
        audit_result: Optional[Dict] = None
    ) -> Optional[Post]:
        """
        Update post status and audit result
        
        Args:
            post_id: Post ID
            status: New status
            audit_result: Audit result data
        
        Returns:
            Updated post if found, None otherwise
        """
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        
        if audit_result:
            update_data["audit_result"] = audit_result
        
        result = await self.posts_collection.find_one_and_update(
            {"post_id": post_id},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info("Updated post status", post_id=post_id, status=status)
            return Post(**result)
        return None
    
    async def delete_post(self, post_id: int) -> bool:
        """
        Soft delete post (set status to deleted)
        
        Args:
            post_id: Post ID
        
        Returns:
            True if deleted, False otherwise
        """
        result = await self.posts_collection.update_one(
            {"post_id": post_id},
            {"$set": {"status": "deleted", "updated_at": datetime.now()}}
        )
        
        if result.modified_count > 0:
            logger.info("Deleted post", post_id=post_id)
            return True
        return False
    
    async def list_posts_by_circle(
        self,
        circle_id: int,
        school_id: int,
        skip: int = 0,
        limit: int = 20,
        status: str = "approved",
        sort_by: str = "latest"
    ) -> List[Post]:
        """
        List posts in a circle with sorting
        
        Args:
            circle_id: Circle ID
            school_id: School ID (for data isolation)
            skip: Number of posts to skip
            limit: Maximum number of posts to return
            status: Post status filter
            sort_by: Sort method (latest, hot, featured)
        
        Returns:
            List of posts
        """
        # Build query filter
        query_filter = {
            "circle_id": circle_id,
            "school_id": school_id,
            "status": status
        }
        
        # Add featured filter if sorting by featured
        if sort_by == "featured":
            query_filter["is_featured"] = True
        
        # Determine sort order
        if sort_by == "latest" or sort_by == "featured":
            # Sort by created_at descending (newest first)
            cursor = self.posts_collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        elif sort_by == "hot":
            # For hot sorting, we need to calculate engagement score
            # We'll fetch more posts and sort in memory
            # Fetch posts from last 7 days for hot calculation
            from datetime import datetime, timedelta
            seven_days_ago = datetime.now() - timedelta(days=7)
            query_filter["created_at"] = {"$gte": seven_days_ago}
            
            # Fetch posts (limit to reasonable number for sorting)
            cursor = self.posts_collection.find(query_filter).limit(skip + limit * 3)
        else:
            # Default to latest
            cursor = self.posts_collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        
        posts = []
        async for post_doc in cursor:
            posts.append(Post(**post_doc))
        
        # If hot sorting, calculate scores and sort in memory
        if sort_by == "hot" and posts:
            posts = self._sort_posts_by_hot_score(posts)
            # Apply pagination after sorting
            posts = posts[skip:skip + limit]
        
        return posts
    
    def _sort_posts_by_hot_score(self, posts: List[Post]) -> List[Post]:
        """
        Sort posts by hot score algorithm
        
        Hot score = (likes * 2 + comments * 3 + shares * 1.5) / (hours_since_creation + 2)^1.5
        
        Args:
            posts: List of posts to sort
        
        Returns:
            Sorted list of posts
        """
        from datetime import datetime
        
        def calculate_hot_score(post: Post) -> float:
            # Calculate engagement score
            engagement = (
                post.like_count * 2 +
                post.comment_count * 3 +
                post.share_count * 1.5
            )
            
            # Calculate hours since creation
            hours_since_creation = (datetime.now() - post.created_at).total_seconds() / 3600
            
            # Apply time decay formula
            # Add 2 to avoid division by zero and reduce impact of very recent posts
            time_factor = (hours_since_creation + 2) ** 1.5
            
            # Calculate hot score
            hot_score = engagement / time_factor if time_factor > 0 else 0
            
            return hot_score
        
        # Sort posts by hot score (descending)
        sorted_posts = sorted(posts, key=calculate_hot_score, reverse=True)
        
        return sorted_posts
    
    async def count_posts_by_circle(
        self,
        circle_id: int,
        school_id: int,
        status: str = "approved",
        is_featured: Optional[bool] = None
    ) -> int:
        """
        Count posts in a circle
        
        Args:
            circle_id: Circle ID
            school_id: School ID
            status: Post status filter
            is_featured: Optional featured filter
        
        Returns:
            Total count of posts
        """
        query_filter = {
            "circle_id": circle_id,
            "school_id": school_id,
            "status": status
        }
        
        if is_featured is not None:
            query_filter["is_featured"] = is_featured
        
        count = await self.posts_collection.count_documents(query_filter)
        return count
    
    async def list_posts_by_author(
        self,
        author_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Post]:
        """
        List posts by author
        
        Args:
            author_id: Author user ID
            skip: Number of posts to skip
            limit: Maximum number of posts to return
        
        Returns:
            List of posts
        """
        cursor = self.posts_collection.find({
            "author_id": author_id,
            "status": {"$ne": "deleted"}
        }).sort("created_at", -1).skip(skip).limit(limit)
        
        posts = []
        async for post_doc in cursor:
            posts.append(Post(**post_doc))
        
        return posts
    
    async def increment_view_count(self, post_id: int) -> bool:
        """Increment post view count"""
        result = await self.posts_collection.update_one(
            {"post_id": post_id},
            {"$inc": {"view_count": 1}}
        )
        return result.modified_count > 0
    
    async def increment_like_count(self, post_id: int, increment: int = 1) -> bool:
        """Increment or decrement post like count"""
        result = await self.posts_collection.update_one(
            {"post_id": post_id},
            {"$inc": {"like_count": increment}}
        )
        return result.modified_count > 0
    
    async def increment_comment_count(self, post_id: int, increment: int = 1) -> bool:
        """Increment or decrement post comment count"""
        result = await self.posts_collection.update_one(
            {"post_id": post_id},
            {"$inc": {"comment_count": increment}}
        )
        return result.modified_count > 0
    
    async def increment_share_count(self, post_id: int) -> bool:
        """Increment post share count"""
        result = await self.posts_collection.update_one(
            {"post_id": post_id},
            {"$inc": {"share_count": 1}}
        )
        return result.modified_count > 0
    
    async def increment_collect_count(self, post_id: int, increment: int = 1) -> bool:
        """Increment or decrement post collect count"""
        result = await self.posts_collection.update_one(
            {"post_id": post_id},
            {"$inc": {"collect_count": increment}}
        )
        return result.modified_count > 0
    
    async def create_comment(self, comment_data: Dict) -> Comment:
        """
        Create a new comment
        
        Args:
            comment_data: Comment data dictionary
        
        Returns:
            Created comment
        """
        # Get next comment ID
        comment_id = await self._get_next_comment_id()
        
        # Prepare comment document
        comment_doc = {
            "comment_id": comment_id,
            "post_id": comment_data["post_id"],
            "author_id": comment_data["author_id"],
            "content": comment_data["content"],
            "parent_id": comment_data.get("parent_id"),
            "reply_to_user_id": comment_data.get("reply_to_user_id"),
            "like_count": 0,
            "is_anonymous": comment_data.get("is_anonymous", False),
            "status": "active",
            "created_at": datetime.now()
        }
        
        # Insert into MongoDB
        result = await self.comments_collection.insert_one(comment_doc)
        comment_doc["_id"] = result.inserted_id
        
        # Increment post comment count
        await self.increment_comment_count(comment_data["post_id"])
        
        logger.info(
            "Created comment",
            comment_id=comment_id,
            post_id=comment_data["post_id"],
            author_id=comment_data["author_id"]
        )
        
        return Comment(**comment_doc)
    
    async def get_comment_by_id(self, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        comment_doc = await self.comments_collection.find_one({"comment_id": comment_id})
        if comment_doc:
            return Comment(**comment_doc)
        return None
    
    async def list_comments_by_post(
        self,
        post_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Comment]:
        """
        List comments for a post
        
        Args:
            post_id: Post ID
            skip: Number of comments to skip
            limit: Maximum number of comments to return
        
        Returns:
            List of comments
        """
        cursor = self.comments_collection.find({
            "post_id": post_id,
            "status": "active"
        }).sort("created_at", 1).skip(skip).limit(limit)
        
        comments = []
        async for comment_doc in cursor:
            comments.append(Comment(**comment_doc))
        
        return comments
    
    async def delete_comment(self, comment_id: int) -> bool:
        """
        Soft delete comment
        
        Args:
            comment_id: Comment ID
        
        Returns:
            True if deleted, False otherwise
        """
        # Get comment to get post_id
        comment = await self.get_comment_by_id(comment_id)
        if not comment:
            return False
        
        # Update comment status
        result = await self.comments_collection.update_one(
            {"comment_id": comment_id},
            {"$set": {"status": "deleted"}}
        )
        
        if result.modified_count > 0:
            # Decrement post comment count
            await self.increment_comment_count(comment.post_id, -1)
            logger.info("Deleted comment", comment_id=comment_id)
            return True
        return False


class InteractionRepository:
    """Repository for interaction operations (likes, collects, shares)"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.interactions_collection = db["interactions"]
    
    async def create_interaction(
        self,
        user_id: int,
        target_type: str,
        target_id: int,
        action_type: str
    ) -> bool:
        """
        Create an interaction record
        
        Args:
            user_id: User ID
            target_type: Target type (post, comment)
            target_id: Target ID
            action_type: Action type (like, collect, share)
        
        Returns:
            True if created, False if already exists
        """
        # Check if interaction already exists
        existing = await self.interactions_collection.find_one({
            "user_id": user_id,
            "target_type": target_type,
            "target_id": target_id,
            "action_type": action_type
        })
        
        if existing:
            return False
        
        # Create interaction
        interaction_doc = {
            "user_id": user_id,
            "target_type": target_type,
            "target_id": target_id,
            "action_type": action_type,
            "created_at": datetime.now()
        }
        
        await self.interactions_collection.insert_one(interaction_doc)
        
        logger.info(
            "Created interaction",
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            action_type=action_type
        )
        
        return True
    
    async def delete_interaction(
        self,
        user_id: int,
        target_type: str,
        target_id: int,
        action_type: str
    ) -> bool:
        """
        Delete an interaction record
        
        Args:
            user_id: User ID
            target_type: Target type (post, comment)
            target_id: Target ID
            action_type: Action type (like, collect)
        
        Returns:
            True if deleted, False if not found
        """
        result = await self.interactions_collection.delete_one({
            "user_id": user_id,
            "target_type": target_type,
            "target_id": target_id,
            "action_type": action_type
        })
        
        if result.deleted_count > 0:
            logger.info(
                "Deleted interaction",
                user_id=user_id,
                target_type=target_type,
                target_id=target_id,
                action_type=action_type
            )
            return True
        return False
    
    async def check_interaction_exists(
        self,
        user_id: int,
        target_type: str,
        target_id: int,
        action_type: str
    ) -> bool:
        """
        Check if an interaction exists
        
        Args:
            user_id: User ID
            target_type: Target type (post, comment)
            target_id: Target ID
            action_type: Action type (like, collect)
        
        Returns:
            True if exists, False otherwise
        """
        existing = await self.interactions_collection.find_one({
            "user_id": user_id,
            "target_type": target_type,
            "target_id": target_id,
            "action_type": action_type
        })
        
        return existing is not None
    
    async def get_user_interactions(
        self,
        user_id: int,
        target_type: str,
        action_type: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get user's interactions
        
        Args:
            user_id: User ID
            target_type: Target type (post, comment)
            action_type: Action type (like, collect)
            skip: Number to skip
            limit: Maximum number to return
        
        Returns:
            List of interaction documents
        """
        cursor = self.interactions_collection.find({
            "user_id": user_id,
            "target_type": target_type,
            "action_type": action_type
        }).sort("created_at", -1).skip(skip).limit(limit)
        
        interactions = []
        async for doc in cursor:
            interactions.append(doc)
        
        return interactions


class RecommendationRepository:
    """Repository for recommendation queries"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.posts_collection = db["posts"]
        self.interactions_collection = db["interactions"]
    
    async def get_posts_by_tags(
        self,
        school_id: int,
        tags: List[str],
        exclude_post_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[Post]:
        """
        Get posts matching user's interest tags
        
        Args:
            school_id: School ID for data isolation
            tags: List of user's interest tags
            exclude_post_ids: Optional list of post IDs to exclude (already viewed)
            limit: Maximum number of posts to return
        
        Returns:
            List of posts matching tags
        """
        if not tags:
            return []
        
        # Build query filter
        query_filter = {
            "school_id": school_id,
            "status": "approved",
            "tags": {"$in": tags}  # Match any of the user's tags
        }
        
        # Exclude already viewed posts
        if exclude_post_ids:
            query_filter["post_id"] = {"$nin": exclude_post_ids}
        
        # Fetch posts from last 30 days for freshness
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        query_filter["created_at"] = {"$gte": thirty_days_ago}
        
        # Fetch posts
        cursor = self.posts_collection.find(query_filter).limit(limit)
        
        posts = []
        async for post_doc in cursor:
            posts.append(Post(**post_doc))
        
        return posts
    
    async def get_hot_posts(
        self,
        school_id: int,
        exclude_post_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[Post]:
        """
        Get hot posts across all circles
        
        Args:
            school_id: School ID for data isolation
            exclude_post_ids: Optional list of post IDs to exclude
            limit: Maximum number of posts to return
        
        Returns:
            List of hot posts
        """
        # Build query filter
        query_filter = {
            "school_id": school_id,
            "status": "approved"
        }
        
        # Exclude already viewed posts
        if exclude_post_ids:
            query_filter["post_id"] = {"$nin": exclude_post_ids}
        
        # Fetch posts from last 7 days for hot calculation
        from datetime import datetime, timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        query_filter["created_at"] = {"$gte": seven_days_ago}
        
        # Fetch posts (we'll sort by hot score in memory)
        cursor = self.posts_collection.find(query_filter).limit(limit * 2)
        
        posts = []
        async for post_doc in cursor:
            posts.append(Post(**post_doc))
        
        # Sort by hot score
        posts = self._sort_posts_by_hot_score(posts)
        
        return posts[:limit]
    
    async def get_posts_by_location(
        self,
        school_id: int,
        campus: Optional[str],
        major: Optional[str],
        exclude_post_ids: Optional[List[int]] = None,
        limit: int = 50
    ) -> List[Post]:
        """
        Get posts from same campus/major (requires author profile lookup)
        
        Note: This is a simplified version. In production, you'd want to:
        1. Store author's campus/major in post document for efficient querying
        2. Or use a separate collection to map user_id -> campus/major
        
        For now, we'll return posts from the same school and let the service
        layer handle the campus/major filtering.
        
        Args:
            school_id: School ID
            campus: User's campus
            major: User's major
            exclude_post_ids: Optional list of post IDs to exclude
            limit: Maximum number of posts to return
        
        Returns:
            List of posts from same school
        """
        # Build query filter
        query_filter = {
            "school_id": school_id,
            "status": "approved"
        }
        
        # Exclude already viewed posts
        if exclude_post_ids:
            query_filter["post_id"] = {"$nin": exclude_post_ids}
        
        # Fetch recent posts
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        query_filter["created_at"] = {"$gte": thirty_days_ago}
        
        cursor = self.posts_collection.find(query_filter).sort("created_at", -1).limit(limit)
        
        posts = []
        async for post_doc in cursor:
            posts.append(Post(**post_doc))
        
        return posts
    
    async def get_user_viewed_posts(
        self,
        user_id: int,
        days: int = 7
    ) -> List[int]:
        """
        Get list of post IDs that user has viewed recently
        
        Args:
            user_id: User ID
            days: Number of days to look back
        
        Returns:
            List of post IDs
        """
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor = self.interactions_collection.find({
            "user_id": user_id,
            "target_type": "post",
            "action_type": "view",
            "created_at": {"$gte": cutoff_date}
        })
        
        viewed_post_ids = []
        async for doc in cursor:
            viewed_post_ids.append(doc["target_id"])
        
        return viewed_post_ids
    
    def _sort_posts_by_hot_score(self, posts: List[Post]) -> List[Post]:
        """
        Sort posts by hot score algorithm
        
        Hot score = (likes * 2 + comments * 3 + shares * 1.5) / (hours_since_creation + 2)^1.5
        
        Args:
            posts: List of posts to sort
        
        Returns:
            Sorted list of posts
        """
        from datetime import datetime
        
        def calculate_hot_score(post: Post) -> float:
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
            hot_score = engagement / time_factor if time_factor > 0 else 0
            
            return hot_score
        
        # Sort posts by hot score (descending)
        sorted_posts = sorted(posts, key=calculate_hot_score, reverse=True)
        
        return sorted_posts
