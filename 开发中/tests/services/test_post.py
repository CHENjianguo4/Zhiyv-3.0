"""
Post Service Tests

Unit tests for post service functionality.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.post import PostService
from app.repositories.post import PostRepository
from app.services.content_audit import ContentAuditEngine, ContentAuditResult
from app.models.post import Post, Comment, AuditResult
from app.core.exceptions import ValidationError, PermissionDeniedError, ResourceNotFoundError


@pytest.fixture
def mock_post_repo():
    """Mock post repository"""
    return AsyncMock(spec=PostRepository)


@pytest.fixture
def mock_audit_engine():
    """Mock content audit engine"""
    return AsyncMock(spec=ContentAuditEngine)


@pytest.fixture
def post_service(mock_post_repo, mock_audit_engine):
    """Post service instance with mocked dependencies"""
    return PostService(mock_post_repo, mock_audit_engine)


@pytest.fixture
def sample_post():
    """Sample post for testing"""
    return Post(
        post_id=1,
        school_id=1,
        circle_id=1,
        author_id=1,
        title="Test Post",
        content="This is a test post",
        type="text",
        images=[],
        videos=[],
        poll_options=[],
        tags=["test"],
        is_anonymous=False,
        status="approved",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_comment():
    """Sample comment for testing"""
    return Comment(
        comment_id=1,
        post_id=1,
        author_id=1,
        content="This is a test comment",
        is_anonymous=False,
        created_at=datetime.now()
    )


class TestCreatePost:
    """Tests for create_post method"""
    
    @pytest.mark.asyncio
    async def test_create_text_post_success(
        self,
        post_service,
        mock_post_repo,
        mock_audit_engine,
        sample_post
    ):
        """Test creating a text post successfully"""
        # Setup
        mock_audit_engine.audit_content.return_value = ContentAuditResult(
            passed=True,
            action="approve"
        )
        mock_post_repo.create_post.return_value = sample_post
        
        # Execute
        result = await post_service.create_post(
            user_id=1,
            school_id=1,
            circle_id=1,
            title="Test Post",
            content="This is a test post",
            post_type="text",
            tags=["test"]
        )
        
        # Assert
        assert result.post_id == 1
        assert result.title == "Test Post"
        assert result.status == "approved"
        mock_audit_engine.audit_content.assert_called_once()
        mock_post_repo.create_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_post_invalid_type(self, post_service):
        """Test creating post with invalid type"""
        with pytest.raises(ValidationError) as exc_info:
            await post_service.create_post(
                user_id=1,
                school_id=1,
                circle_id=1,
                title="Test",
                content="Test",
                post_type="invalid_type"
            )
        assert "Invalid post type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_image_post_without_images(self, post_service):
        """Test creating image post without images"""
        with pytest.raises(ValidationError) as exc_info:
            await post_service.create_post(
                user_id=1,
                school_id=1,
                circle_id=1,
                title="Test",
                content="Test",
                post_type="image"
            )
        assert "must include at least one image" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_post_title_too_long(self, post_service):
        """Test creating post with title exceeding max length"""
        with pytest.raises(ValidationError) as exc_info:
            await post_service.create_post(
                user_id=1,
                school_id=1,
                circle_id=1,
                title="x" * 201,  # Exceeds 200 character limit
                content="Test",
                post_type="text"
            )
        assert "cannot exceed 200 characters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_post_content_too_long(self, post_service):
        """Test creating post with content exceeding max length"""
        with pytest.raises(ValidationError) as exc_info:
            await post_service.create_post(
                user_id=1,
                school_id=1,
                circle_id=1,
                title="Test",
                content="x" * 5001,  # Exceeds 5000 character limit
                post_type="text"
            )
        assert "cannot exceed 5000 characters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_post_blocked_by_audit(
        self,
        post_service,
        mock_audit_engine
    ):
        """Test creating post blocked by content audit"""
        # Setup
        mock_audit_engine.audit_content.return_value = ContentAuditResult(
            passed=False,
            action="block",
            found_words=["敏感词"]
        )
        
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await post_service.create_post(
                user_id=1,
                school_id=1,
                circle_id=1,
                title="Test",
                content="Contains 敏感词",
                post_type="text"
            )
        assert "sensitive words" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_draft_post(
        self,
        post_service,
        mock_post_repo,
        sample_post
    ):
        """Test creating a draft post (no audit)"""
        # Setup
        draft_post = Post(**sample_post.model_dump())
        draft_post.status = "draft"
        mock_post_repo.create_post.return_value = draft_post
        
        # Execute
        result = await post_service.create_post(
            user_id=1,
            school_id=1,
            circle_id=1,
            title="Draft Post",
            content="This is a draft",
            post_type="text",
            is_draft=True
        )
        
        # Assert
        assert result.status == "draft"
        mock_post_repo.create_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_anonymous_post(
        self,
        post_service,
        mock_post_repo,
        mock_audit_engine,
        sample_post
    ):
        """Test creating an anonymous post"""
        # Setup
        mock_audit_engine.audit_content.return_value = ContentAuditResult(
            passed=True,
            action="approve"
        )
        anon_post = Post(**sample_post.model_dump())
        anon_post.is_anonymous = True
        mock_post_repo.create_post.return_value = anon_post
        
        # Execute
        result = await post_service.create_post(
            user_id=1,
            school_id=1,
            circle_id=1,
            title="Anonymous Post",
            content="This is anonymous",
            post_type="text",
            is_anonymous=True
        )
        
        # Assert
        assert result.is_anonymous is True


class TestUpdatePost:
    """Tests for update_post method"""
    
    @pytest.mark.asyncio
    async def test_update_post_success(
        self,
        post_service,
        mock_post_repo,
        mock_audit_engine,
        sample_post
    ):
        """Test updating post successfully"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_audit_engine.audit_content.return_value = ContentAuditResult(
            passed=True,
            action="approve"
        )
        updated_post = Post(**sample_post.model_dump())
        updated_post.title = "Updated Title"
        mock_post_repo.update_post.return_value = updated_post
        
        # Execute
        result = await post_service.update_post(
            post_id=1,
            user_id=1,
            title="Updated Title"
        )
        
        # Assert
        assert result.title == "Updated Title"
        mock_post_repo.update_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_post_not_found(
        self,
        post_service,
        mock_post_repo
    ):
        """Test updating non-existent post"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = None
        
        # Execute & Assert
        with pytest.raises(ResourceNotFoundError):
            await post_service.update_post(
                post_id=999,
                user_id=1,
                title="Updated"
            )
    
    @pytest.mark.asyncio
    async def test_update_post_permission_denied(
        self,
        post_service,
        mock_post_repo,
        sample_post
    ):
        """Test updating post by non-author"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        
        # Execute & Assert
        with pytest.raises(PermissionDeniedError):
            await post_service.update_post(
                post_id=1,
                user_id=999,  # Different user
                title="Updated"
            )


class TestDeletePost:
    """Tests for delete_post method"""
    
    @pytest.mark.asyncio
    async def test_delete_post_success(
        self,
        post_service,
        mock_post_repo,
        sample_post
    ):
        """Test deleting post successfully"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_post_repo.delete_post.return_value = True
        
        # Execute
        result = await post_service.delete_post(post_id=1, user_id=1)
        
        # Assert
        assert result is True
        mock_post_repo.delete_post.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_delete_post_permission_denied(
        self,
        post_service,
        mock_post_repo,
        sample_post
    ):
        """Test deleting post by non-author"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        
        # Execute & Assert
        with pytest.raises(PermissionDeniedError):
            await post_service.delete_post(post_id=1, user_id=999)


class TestCreateComment:
    """Tests for create_comment method"""
    
    @pytest.mark.asyncio
    async def test_create_comment_success(
        self,
        post_service,
        mock_post_repo,
        mock_audit_engine,
        sample_post,
        sample_comment
    ):
        """Test creating comment successfully"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_audit_engine.audit_text.return_value = ContentAuditResult(
            passed=True,
            action="approve"
        )
        mock_post_repo.create_comment.return_value = sample_comment
        
        # Execute
        result = await post_service.create_comment(
            post_id=1,
            user_id=1,
            content="Test comment"
        )
        
        # Assert
        assert result.comment_id == 1
        assert result.content == "This is a test comment"
        mock_post_repo.create_comment.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_comment_post_not_found(
        self,
        post_service,
        mock_post_repo
    ):
        """Test creating comment on non-existent post"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = None
        
        # Execute & Assert
        with pytest.raises(ResourceNotFoundError):
            await post_service.create_comment(
                post_id=999,
                user_id=1,
                content="Test"
            )
    
    @pytest.mark.asyncio
    async def test_create_comment_too_long(
        self,
        post_service,
        mock_post_repo,
        sample_post
    ):
        """Test creating comment exceeding max length"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await post_service.create_comment(
                post_id=1,
                user_id=1,
                content="x" * 501  # Exceeds 500 character limit
            )
        assert "cannot exceed 500 characters" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_comment_blocked_by_audit(
        self,
        post_service,
        mock_post_repo,
        mock_audit_engine,
        sample_post
    ):
        """Test creating comment blocked by audit"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_audit_engine.audit_text.return_value = ContentAuditResult(
            passed=False,
            action="block",
            found_words=["敏感词"]
        )
        
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await post_service.create_comment(
                post_id=1,
                user_id=1,
                content="Contains 敏感词"
            )
        assert "sensitive words" in str(exc_info.value)


class TestPublishDraft:
    """Tests for publish_draft method"""
    
    @pytest.mark.asyncio
    async def test_publish_draft_success(
        self,
        post_service,
        mock_post_repo,
        mock_audit_engine,
        sample_post
    ):
        """Test publishing draft successfully"""
        # Setup
        draft_post = Post(**sample_post.model_dump())
        draft_post.status = "draft"
        mock_post_repo.get_post_by_id.return_value = draft_post
        mock_audit_engine.audit_content.return_value = ContentAuditResult(
            passed=True,
            action="approve"
        )
        published_post = Post(**draft_post.model_dump())
        published_post.status = "approved"
        mock_post_repo.update_post_status.return_value = published_post
        
        # Execute
        result = await post_service.publish_draft(post_id=1, user_id=1)
        
        # Assert
        assert result.status == "approved"
        mock_post_repo.update_post_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_draft_not_draft(
        self,
        post_service,
        mock_post_repo,
        sample_post
    ):
        """Test publishing non-draft post"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post  # Already approved
        
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await post_service.publish_draft(post_id=1, user_id=1)
        assert "Only draft posts can be published" in str(exc_info.value)



class TestPostInteractions:
    """Tests for post interaction methods"""
    
    @pytest.fixture
    def mock_interaction_repo(self):
        """Mock interaction repository"""
        from app.repositories.post import InteractionRepository
        return AsyncMock(spec=InteractionRepository)
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        from redis.asyncio import Redis
        return AsyncMock(spec=Redis)
    
    @pytest.fixture
    def post_service_with_interactions(
        self,
        mock_post_repo,
        mock_audit_engine,
        mock_interaction_repo,
        mock_redis
    ):
        """Post service with interaction support"""
        return PostService(
            mock_post_repo,
            mock_audit_engine,
            mock_interaction_repo,
            mock_redis
        )
    
    @pytest.mark.asyncio
    async def test_like_post_success(
        self,
        post_service_with_interactions,
        mock_post_repo,
        mock_interaction_repo,
        mock_redis,
        sample_post
    ):
        """Test liking a post successfully"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_interaction_repo.check_interaction_exists.return_value = False
        mock_interaction_repo.create_interaction.return_value = True
        mock_post_repo.increment_like_count.return_value = True
        
        updated_post = Post(**sample_post.model_dump())
        updated_post.like_count = 1
        mock_post_repo.get_post_by_id.return_value = updated_post
        
        # Execute
        result = await post_service_with_interactions.like_post(post_id=1, user_id=1)
        
        # Assert
        assert result["liked"] is True
        assert result["like_count"] == 1
        mock_interaction_repo.create_interaction.assert_called_once()
        mock_post_repo.increment_like_count.assert_called_once_with(1, 1)
    
    @pytest.mark.asyncio
    async def test_unlike_post_success(
        self,
        post_service_with_interactions,
        mock_post_repo,
        mock_interaction_repo,
        mock_redis,
        sample_post
    ):
        """Test unliking a post successfully"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_interaction_repo.check_interaction_exists.return_value = True
        mock_interaction_repo.delete_interaction.return_value = True
        mock_post_repo.increment_like_count.return_value = True
        
        updated_post = Post(**sample_post.model_dump())
        updated_post.like_count = 0
        mock_post_repo.get_post_by_id.return_value = updated_post
        
        # Execute
        result = await post_service_with_interactions.like_post(post_id=1, user_id=1)
        
        # Assert
        assert result["liked"] is False
        assert result["like_count"] == 0
        mock_interaction_repo.delete_interaction.assert_called_once()
        mock_post_repo.increment_like_count.assert_called_once_with(1, -1)
    
    @pytest.mark.asyncio
    async def test_like_post_not_found(
        self,
        post_service_with_interactions,
        mock_post_repo
    ):
        """Test liking non-existent post"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = None
        
        # Execute & Assert
        with pytest.raises(ResourceNotFoundError):
            await post_service_with_interactions.like_post(post_id=999, user_id=1)
    
    @pytest.mark.asyncio
    async def test_collect_post_success(
        self,
        post_service_with_interactions,
        mock_post_repo,
        mock_interaction_repo,
        mock_redis,
        sample_post
    ):
        """Test collecting a post successfully"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_interaction_repo.check_interaction_exists.return_value = False
        mock_interaction_repo.create_interaction.return_value = True
        mock_post_repo.increment_collect_count.return_value = True
        
        updated_post = Post(**sample_post.model_dump())
        updated_post.collect_count = 1
        mock_post_repo.get_post_by_id.return_value = updated_post
        
        # Execute
        result = await post_service_with_interactions.collect_post(post_id=1, user_id=1)
        
        # Assert
        assert result["collected"] is True
        assert result["collect_count"] == 1
        mock_interaction_repo.create_interaction.assert_called_once()
        mock_post_repo.increment_collect_count.assert_called_once_with(1, 1)
    
    @pytest.mark.asyncio
    async def test_share_post_success(
        self,
        post_service_with_interactions,
        mock_post_repo,
        mock_interaction_repo,
        mock_redis,
        sample_post
    ):
        """Test sharing a post successfully"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_interaction_repo.create_interaction.return_value = True
        mock_post_repo.increment_share_count.return_value = True
        
        updated_post = Post(**sample_post.model_dump())
        updated_post.share_count = 1
        mock_post_repo.get_post_by_id.return_value = updated_post
        
        # Execute
        result = await post_service_with_interactions.share_post(post_id=1, user_id=1)
        
        # Assert
        assert result["share_count"] == 1
        mock_interaction_repo.create_interaction.assert_called_once()
        mock_post_repo.increment_share_count.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_forward_post_success(
        self,
        post_service_with_interactions,
        mock_post_repo,
        mock_audit_engine,
        sample_post
    ):
        """Test forwarding a post successfully"""
        # Setup
        mock_post_repo.get_post_by_id.return_value = sample_post
        mock_audit_engine.audit_content.return_value = ContentAuditResult(
            passed=True,
            action="approve"
        )
        
        forwarded_post = Post(**sample_post.model_dump())
        forwarded_post.post_id = 2
        forwarded_post.title = f"[转发] {sample_post.title}"
        mock_post_repo.create_post.return_value = forwarded_post
        mock_post_repo.increment_share_count.return_value = True
        
        # Execute
        result = await post_service_with_interactions.forward_post(
            post_id=1,
            user_id=1,
            school_id=1,
            target_circle_id=2,
            forward_comment="Great post!"
        )
        
        # Assert
        assert result.post_id == 2
        assert "[转发]" in result.title
        mock_post_repo.create_post.assert_called_once()
        mock_post_repo.increment_share_count.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_user_interactions(
        self,
        post_service_with_interactions,
        mock_interaction_repo
    ):
        """Test checking user interactions with a post"""
        # Setup
        mock_interaction_repo.check_interaction_exists.side_effect = [True, False]
        
        # Execute
        result = await post_service_with_interactions.check_user_interactions(
            user_id=1,
            post_id=1
        )
        
        # Assert
        assert result["liked"] is True
        assert result["collected"] is False
        assert mock_interaction_repo.check_interaction_exists.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_user_liked_posts(
        self,
        post_service_with_interactions,
        mock_interaction_repo
    ):
        """Test getting user's liked posts"""
        # Setup
        mock_interaction_repo.get_user_interactions.return_value = [
            {"target_id": 1},
            {"target_id": 2},
            {"target_id": 3}
        ]
        
        # Execute
        result = await post_service_with_interactions.get_user_liked_posts(
            user_id=1,
            page=1,
            page_size=20
        )
        
        # Assert
        assert result == [1, 2, 3]
        mock_interaction_repo.get_user_interactions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_collected_posts(
        self,
        post_service_with_interactions,
        mock_interaction_repo
    ):
        """Test getting user's collected posts"""
        # Setup
        mock_interaction_repo.get_user_interactions.return_value = [
            {"target_id": 5},
            {"target_id": 6}
        ]
        
        # Execute
        result = await post_service_with_interactions.get_user_collected_posts(
            user_id=1,
            page=1,
            page_size=20
        )
        
        # Assert
        assert result == [5, 6]
        mock_interaction_repo.get_user_interactions.assert_called_once()


class TestPostSorting:
    """Tests for post sorting functionality"""
    
    @pytest.mark.asyncio
    async def test_list_circle_posts_latest_sort(
        self,
        post_service,
        mock_post_repo
    ):
        """Test listing posts with latest sorting"""
        # Setup
        posts = [
            Post(
                post_id=i,
                school_id=1,
                circle_id=1,
                author_id=1,
                title=f"Post {i}",
                content=f"Content {i}",
                type="text",
                status="approved",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(1, 4)
        ]
        mock_post_repo.list_posts_by_circle.return_value = posts
        mock_post_repo.count_posts_by_circle.return_value = 3
        
        # Execute
        result_posts, total = await post_service.list_circle_posts(
            circle_id=1,
            school_id=1,
            page=1,
            page_size=20,
            sort_by="latest"
        )
        
        # Assert
        assert len(result_posts) == 3
        assert total == 3
        mock_post_repo.list_posts_by_circle.assert_called_once_with(
            circle_id=1,
            school_id=1,
            skip=0,
            limit=20,
            status="approved",
            sort_by="latest"
        )
        mock_post_repo.count_posts_by_circle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_circle_posts_hot_sort(
        self,
        post_service,
        mock_post_repo
    ):
        """Test listing posts with hot sorting"""
        # Setup
        posts = [
            Post(
                post_id=1,
                school_id=1,
                circle_id=1,
                author_id=1,
                title="Hot Post",
                content="Very popular",
                type="text",
                status="approved",
                like_count=100,
                comment_count=50,
                share_count=20,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Post(
                post_id=2,
                school_id=1,
                circle_id=1,
                author_id=1,
                title="Less Hot Post",
                content="Less popular",
                type="text",
                status="approved",
                like_count=10,
                comment_count=5,
                share_count=2,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_post_repo.list_posts_by_circle.return_value = posts
        mock_post_repo.count_posts_by_circle.return_value = 2
        
        # Execute
        result_posts, total = await post_service.list_circle_posts(
            circle_id=1,
            school_id=1,
            page=1,
            page_size=20,
            sort_by="hot"
        )
        
        # Assert
        assert len(result_posts) == 2
        assert total == 2
        mock_post_repo.list_posts_by_circle.assert_called_once_with(
            circle_id=1,
            school_id=1,
            skip=0,
            limit=20,
            status="approved",
            sort_by="hot"
        )
    
    @pytest.mark.asyncio
    async def test_list_circle_posts_featured_sort(
        self,
        post_service,
        mock_post_repo
    ):
        """Test listing posts with featured sorting"""
        # Setup
        posts = [
            Post(
                post_id=1,
                school_id=1,
                circle_id=1,
                author_id=1,
                title="Featured Post",
                content="This is featured",
                type="text",
                status="approved",
                is_featured=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        mock_post_repo.list_posts_by_circle.return_value = posts
        mock_post_repo.count_posts_by_circle.return_value = 1
        
        # Execute
        result_posts, total = await post_service.list_circle_posts(
            circle_id=1,
            school_id=1,
            page=1,
            page_size=20,
            sort_by="featured"
        )
        
        # Assert
        assert len(result_posts) == 1
        assert result_posts[0].is_featured is True
        assert total == 1
        mock_post_repo.list_posts_by_circle.assert_called_once_with(
            circle_id=1,
            school_id=1,
            skip=0,
            limit=20,
            status="approved",
            sort_by="featured"
        )
        # Verify featured filter was passed to count
        mock_post_repo.count_posts_by_circle.assert_called_once_with(
            circle_id=1,
            school_id=1,
            status="approved",
            is_featured=True
        )
    
    @pytest.mark.asyncio
    async def test_list_circle_posts_invalid_sort(
        self,
        post_service
    ):
        """Test listing posts with invalid sort parameter"""
        # Execute & Assert
        with pytest.raises(ValidationError) as exc_info:
            await post_service.list_circle_posts(
                circle_id=1,
                school_id=1,
                page=1,
                page_size=20,
                sort_by="invalid_sort"
            )
        assert "Invalid sort_by" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_list_circle_posts_pagination(
        self,
        post_service,
        mock_post_repo
    ):
        """Test listing posts with pagination"""
        # Setup
        posts = [
            Post(
                post_id=i,
                school_id=1,
                circle_id=1,
                author_id=1,
                title=f"Post {i}",
                content=f"Content {i}",
                type="text",
                status="approved",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(21, 31)  # Page 2 posts (11-20)
        ]
        mock_post_repo.list_posts_by_circle.return_value = posts
        mock_post_repo.count_posts_by_circle.return_value = 50
        
        # Execute
        result_posts, total = await post_service.list_circle_posts(
            circle_id=1,
            school_id=1,
            page=2,
            page_size=10,
            sort_by="latest"
        )
        
        # Assert
        assert len(result_posts) == 10
        assert total == 50
        # Verify skip calculation for page 2
        mock_post_repo.list_posts_by_circle.assert_called_once_with(
            circle_id=1,
            school_id=1,
            skip=10,  # (page 2 - 1) * 10
            limit=10,
            status="approved",
            sort_by="latest"
        )


class TestHotScoreCalculation:
    """Tests for hot score calculation algorithm"""
    
    def test_hot_score_calculation_high_engagement(self):
        """Test hot score for post with high engagement"""
        from datetime import datetime, timedelta
        
        # Create a mock repository to access the sorting method
        class MockDB:
            def __getitem__(self, key):
                return None
        
        from app.repositories.post import PostRepository
        repo = PostRepository(MockDB())
        
        # Create a post with high engagement from 2 hours ago
        post = Post(
            post_id=1,
            school_id=1,
            circle_id=1,
            author_id=1,
            title="Hot Post",
            content="Very popular",
            type="text",
            status="approved",
            like_count=100,
            comment_count=50,
            share_count=20,
            created_at=datetime.now() - timedelta(hours=2),
            updated_at=datetime.now()
        )
        
        # Calculate expected score
        # engagement = 100*2 + 50*3 + 20*1.5 = 200 + 150 + 30 = 380
        # time_factor = (2 + 2)^1.5 = 4^1.5 = 8
        # hot_score = 380 / 8 = 47.5
        
        posts = [post]
        sorted_posts = repo._sort_posts_by_hot_score(posts)
        
        assert len(sorted_posts) == 1
        assert sorted_posts[0].post_id == 1
    
    def test_hot_score_calculation_multiple_posts(self):
        """Test hot score sorting with multiple posts"""
        from datetime import datetime, timedelta
        
        # Create a mock repository to access the sorting method
        class MockDB:
            def __getitem__(self, key):
                return None
        
        from app.repositories.post import PostRepository
        repo = PostRepository(MockDB())
        
        # Create posts with different engagement and ages
        posts = [
            Post(
                post_id=1,
                school_id=1,
                circle_id=1,
                author_id=1,
                title="Old Popular Post",
                content="Old but popular",
                type="text",
                status="approved",
                like_count=200,
                comment_count=100,
                share_count=50,
                created_at=datetime.now() - timedelta(hours=24),
                updated_at=datetime.now()
            ),
            Post(
                post_id=2,
                school_id=1,
                circle_id=1,
                author_id=1,
                title="Recent Hot Post",
                content="Recent and hot",
                type="text",
                status="approved",
                like_count=50,
                comment_count=30,
                share_count=10,
                created_at=datetime.now() - timedelta(hours=1),
                updated_at=datetime.now()
            ),
            Post(
                post_id=3,
                school_id=1,
                circle_id=1,
                author_id=1,
                title="Low Engagement Post",
                content="Not popular",
                type="text",
                status="approved",
                like_count=5,
                comment_count=2,
                share_count=1,
                created_at=datetime.now() - timedelta(hours=3),
                updated_at=datetime.now()
            )
        ]
        
        sorted_posts = repo._sort_posts_by_hot_score(posts)
        
        # Verify posts are sorted by hot score
        assert len(sorted_posts) == 3
        # Recent hot post should rank higher due to recency
        assert sorted_posts[0].post_id == 2
        # Low engagement post should be last
        assert sorted_posts[2].post_id == 3
    
    def test_hot_score_zero_engagement(self):
        """Test hot score for post with zero engagement"""
        from datetime import datetime, timedelta
        
        # Create a mock repository to access the sorting method
        class MockDB:
            def __getitem__(self, key):
                return None
        
        from app.repositories.post import PostRepository
        repo = PostRepository(MockDB())
        
        post = Post(
            post_id=1,
            school_id=1,
            circle_id=1,
            author_id=1,
            title="No Engagement Post",
            content="Nobody likes this",
            type="text",
            status="approved",
            like_count=0,
            comment_count=0,
            share_count=0,
            created_at=datetime.now() - timedelta(hours=5),
            updated_at=datetime.now()
        )
        
        posts = [post]
        sorted_posts = repo._sort_posts_by_hot_score(posts)
        
        # Should not crash with zero engagement
        assert len(sorted_posts) == 1
        assert sorted_posts[0].post_id == 1
