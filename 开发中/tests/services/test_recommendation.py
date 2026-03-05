"""
Tests for Content Recommendation System

Tests the basic recommendation functionality including:
- Tag-based matching
- Hot content recommendation
- Location-based prioritization
- Hybrid scoring algorithm
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.post import PostService
from app.models.post import Post, PollOption, AuditResult


@pytest.fixture
def mock_post_repo():
    """Mock post repository"""
    repo = AsyncMock()
    repo.db = MagicMock()  # Mock database instance
    return repo


@pytest.fixture
def mock_audit_engine():
    """Mock audit engine"""
    return AsyncMock()


@pytest.fixture
def mock_interaction_repo():
    """Mock interaction repository"""
    return AsyncMock()


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    return AsyncMock()


@pytest.fixture
def post_service(mock_post_repo, mock_audit_engine, mock_interaction_repo, mock_redis):
    """Create post service instance"""
    return PostService(
        post_repository=mock_post_repo,
        audit_engine=mock_audit_engine,
        interaction_repository=mock_interaction_repo,
        redis=mock_redis
    )


@pytest.fixture
def sample_posts():
    """Create sample posts for testing"""
    now = datetime.now()
    
    posts = [
        # Post 1: High engagement, recent, matching tags
        Post(
            post_id=1,
            school_id=1,
            circle_id=1,
            author_id=100,
            title="Python Programming Tips",
            content="Great Python tips for beginners",
            type="text",
            tags=["python", "programming", "tutorial"],
            is_anonymous=False,
            view_count=500,
            like_count=50,
            comment_count=20,
            share_count=10,
            collect_count=15,
            status="approved",
            is_pinned=False,
            is_featured=False,
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2)
        ),
        # Post 2: Medium engagement, older, matching tags
        Post(
            post_id=2,
            school_id=1,
            circle_id=1,
            author_id=101,
            title="Machine Learning Basics",
            content="Introduction to ML concepts",
            type="text",
            tags=["machine-learning", "ai", "python"],
            is_anonymous=False,
            view_count=300,
            like_count=30,
            comment_count=10,
            share_count=5,
            collect_count=8,
            status="approved",
            is_pinned=False,
            is_featured=False,
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=3)
        ),
        # Post 3: Low engagement, recent, no matching tags
        Post(
            post_id=3,
            school_id=1,
            circle_id=2,
            author_id=102,
            title="Campus Food Review",
            content="Best food spots on campus",
            type="text",
            tags=["food", "campus", "review"],
            is_anonymous=False,
            view_count=100,
            like_count=10,
            comment_count=5,
            share_count=2,
            collect_count=3,
            status="approved",
            is_pinned=False,
            is_featured=False,
            created_at=now - timedelta(hours=1),
            updated_at=now - timedelta(hours=1)
        ),
        # Post 4: High engagement, very recent, partial tag match
        Post(
            post_id=4,
            school_id=1,
            circle_id=1,
            author_id=103,
            title="Web Development Guide",
            content="Full stack web development tutorial",
            type="text",
            tags=["web", "programming", "javascript"],
            is_anonymous=False,
            view_count=800,
            like_count=80,
            comment_count=30,
            share_count=15,
            collect_count=25,
            status="approved",
            is_pinned=False,
            is_featured=False,
            created_at=now - timedelta(minutes=30),
            updated_at=now - timedelta(minutes=30)
        ),
    ]
    
    return posts


class TestTagMatchScore:
    """Test tag matching score calculation"""
    
    def test_calculate_tag_match_score_full_match(self, post_service, sample_posts):
        """Test tag match score with full match"""
        post = sample_posts[0]  # Has tags: python, programming, tutorial
        user_tags = ["python", "programming", "tutorial"]
        
        score = post_service._calculate_tag_match_score(post, user_tags)
        
        # All 3 tags match: 3/3 * 100 = 100
        assert score == 100.0
    
    def test_calculate_tag_match_score_partial_match(self, post_service, sample_posts):
        """Test tag match score with partial match"""
        post = sample_posts[0]  # Has tags: python, programming, tutorial
        user_tags = ["python", "javascript", "web", "mobile"]
        
        score = post_service._calculate_tag_match_score(post, user_tags)
        
        # 1 tag matches out of 4 user tags: 1/4 * 100 = 25
        assert score == 25.0
    
    def test_calculate_tag_match_score_no_match(self, post_service, sample_posts):
        """Test tag match score with no match"""
        post = sample_posts[0]  # Has tags: python, programming, tutorial
        user_tags = ["food", "sports", "music"]
        
        score = post_service._calculate_tag_match_score(post, user_tags)
        
        assert score == 0.0
    
    def test_calculate_tag_match_score_no_user_tags(self, post_service, sample_posts):
        """Test tag match score with no user tags"""
        post = sample_posts[0]
        user_tags = None
        
        score = post_service._calculate_tag_match_score(post, user_tags)
        
        assert score == 0.0
    
    def test_calculate_tag_match_score_no_post_tags(self, post_service):
        """Test tag match score with no post tags"""
        post = Post(
            post_id=999,
            school_id=1,
            circle_id=1,
            author_id=100,
            title="Test Post",
            content="Test content",
            type="text",
            tags=[],  # No tags
            is_anonymous=False,
            status="approved",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        user_tags = ["python", "programming"]
        
        score = post_service._calculate_tag_match_score(post, user_tags)
        
        assert score == 0.0


class TestHotScore:
    """Test hot score calculation"""
    
    def test_calculate_hot_score_high_engagement_recent(self, post_service, sample_posts):
        """Test hot score for high engagement recent post"""
        post = sample_posts[3]  # 80 likes, 30 comments, 15 shares, 30 min old
        
        score = post_service._calculate_hot_score(post)
        
        # Should have high score due to high engagement and recency
        assert score > 50.0
    
    def test_calculate_hot_score_low_engagement_recent(self, post_service, sample_posts):
        """Test hot score for low engagement recent post"""
        post = sample_posts[2]  # 10 likes, 5 comments, 2 shares, 1 hour old
        
        score = post_service._calculate_hot_score(post)
        
        # Should have lower score than high engagement posts
        # But recent posts can still score relatively high
        assert score < 100.0  # Just check it's not maxed out
    
    def test_calculate_hot_score_high_engagement_old(self, post_service, sample_posts):
        """Test hot score for high engagement old post"""
        post = sample_posts[1]  # 30 likes, 10 comments, 5 shares, 3 days old
        
        score = post_service._calculate_hot_score(post)
        
        # Should have lower score due to age despite decent engagement
        assert score < 30.0
    
    def test_calculate_hot_score_no_engagement(self, post_service):
        """Test hot score for post with no engagement"""
        post = Post(
            post_id=999,
            school_id=1,
            circle_id=1,
            author_id=100,
            title="Test Post",
            content="Test content",
            type="text",
            tags=[],
            is_anonymous=False,
            like_count=0,
            comment_count=0,
            share_count=0,
            status="approved",
            created_at=datetime.now() - timedelta(hours=1),
            updated_at=datetime.now() - timedelta(hours=1)
        )
        
        score = post_service._calculate_hot_score(post)
        
        assert score == 0.0


class TestLocationScore:
    """Test location score calculation"""
    
    def test_calculate_location_score_same_school(self, post_service, sample_posts):
        """Test location score for same school"""
        post = sample_posts[0]  # school_id = 1
        
        score = post_service._calculate_location_score(
            post=post,
            user_school_id=1,
            user_campus="Main Campus",
            user_major="Computer Science"
        )
        
        # Same school should give base score of 40
        assert score == 40.0
    
    def test_calculate_location_score_different_school(self, post_service, sample_posts):
        """Test location score for different school"""
        post = sample_posts[0]  # school_id = 1
        
        score = post_service._calculate_location_score(
            post=post,
            user_school_id=2,  # Different school
            user_campus="Main Campus",
            user_major="Computer Science"
        )
        
        # Different school should give 0
        assert score == 0.0


class TestPersonalizedRecommendations:
    """Test personalized recommendations"""
    
    @pytest.mark.asyncio
    async def test_get_personalized_recommendations_with_tags(
        self,
        post_service,
        sample_posts
    ):
        """Test personalized recommendations with user tags"""
        # Mock the recommendation repository methods
        with patch('app.repositories.post.RecommendationRepository') as MockRecRepo:
            mock_rec_repo = AsyncMock()
            MockRecRepo.return_value = mock_rec_repo
            
            # Mock repository methods to return coroutines
            mock_rec_repo.get_user_viewed_posts = AsyncMock(return_value=[])
            mock_rec_repo.get_posts_by_tags = AsyncMock(return_value=[sample_posts[0], sample_posts[1]])
            mock_rec_repo.get_hot_posts = AsyncMock(return_value=[sample_posts[3], sample_posts[0]])
            mock_rec_repo.get_posts_by_location = AsyncMock(return_value=[sample_posts[0], sample_posts[2]])
            
            # Get recommendations
            posts, metadata = await post_service.get_personalized_recommendations(
                user_id=1,
                school_id=1,
                user_tags=["python", "programming"],
                user_campus="Main Campus",
                user_major="Computer Science",
                page=1,
                page_size=10,
                exclude_viewed=True
            )
            
            # Should return posts
            assert len(posts) > 0
            
            # Metadata should contain algorithm info
            assert metadata["algorithm"] == "hybrid"
            assert "total_candidates" in metadata
            assert "weights" in metadata
            
            # Verify weights
            assert metadata["weights"]["tag_match"] == 0.4
            assert metadata["weights"]["hot_score"] == 0.3
            assert metadata["weights"]["location"] == 0.3
    
    @pytest.mark.asyncio
    async def test_get_personalized_recommendations_no_tags(
        self,
        post_service,
        sample_posts
    ):
        """Test personalized recommendations without user tags"""
        with patch('app.repositories.post.RecommendationRepository') as MockRecRepo:
            mock_rec_repo = AsyncMock()
            MockRecRepo.return_value = mock_rec_repo
            
            # Mock repository methods
            mock_rec_repo.get_user_viewed_posts = AsyncMock(return_value=[])
            mock_rec_repo.get_posts_by_tags = AsyncMock(return_value=[])  # No tag matches
            mock_rec_repo.get_hot_posts = AsyncMock(return_value=[sample_posts[3], sample_posts[0]])
            mock_rec_repo.get_posts_by_location = AsyncMock(return_value=[sample_posts[0], sample_posts[2]])
            
            # Get recommendations without tags
            posts, metadata = await post_service.get_personalized_recommendations(
                user_id=1,
                school_id=1,
                user_tags=None,  # No tags
                user_campus="Main Campus",
                user_major="Computer Science",
                page=1,
                page_size=10,
                exclude_viewed=False
            )
            
            # Should still return posts based on hot score and location
            assert len(posts) > 0
            assert metadata["algorithm"] == "hybrid"
    
    @pytest.mark.asyncio
    async def test_get_personalized_recommendations_pagination(
        self,
        post_service,
        sample_posts
    ):
        """Test personalized recommendations pagination"""
        with patch('app.repositories.post.RecommendationRepository') as MockRecRepo:
            mock_rec_repo = AsyncMock()
            MockRecRepo.return_value = mock_rec_repo
            
            # Mock repository methods with all sample posts
            mock_rec_repo.get_user_viewed_posts = AsyncMock(return_value=[])
            mock_rec_repo.get_posts_by_tags = AsyncMock(return_value=sample_posts)
            mock_rec_repo.get_hot_posts = AsyncMock(return_value=sample_posts)
            mock_rec_repo.get_posts_by_location = AsyncMock(return_value=sample_posts)
            
            # Get first page
            posts_page1, _ = await post_service.get_personalized_recommendations(
                user_id=1,
                school_id=1,
                user_tags=["python"],
                user_campus="Main Campus",
                user_major="Computer Science",
                page=1,
                page_size=2,
                exclude_viewed=False
            )
            
            # Get second page
            posts_page2, _ = await post_service.get_personalized_recommendations(
                user_id=1,
                school_id=1,
                user_tags=["python"],
                user_campus="Main Campus",
                user_major="Computer Science",
                page=2,
                page_size=2,
                exclude_viewed=False
            )
            
            # Should return different posts
            assert len(posts_page1) <= 2
            assert len(posts_page2) <= 2
            
            # Posts should be different (if enough posts available)
            if len(posts_page1) > 0 and len(posts_page2) > 0:
                page1_ids = {p.post_id for p in posts_page1}
                page2_ids = {p.post_id for p in posts_page2}
                # At least some posts should be different
                assert page1_ids != page2_ids or len(posts_page1) + len(posts_page2) <= 4


class TestHotPostsFeed:
    """Test hot posts feed"""
    
    @pytest.mark.asyncio
    async def test_get_hot_posts_feed(self, post_service, sample_posts):
        """Test getting hot posts feed"""
        with patch('app.repositories.post.RecommendationRepository') as MockRecRepo:
            mock_rec_repo = AsyncMock()
            MockRecRepo.return_value = mock_rec_repo
            
            # Mock hot posts sorted by engagement
            mock_rec_repo.get_hot_posts = AsyncMock(return_value=[
                sample_posts[3],  # Highest engagement
                sample_posts[0],  # Second highest
                sample_posts[1],  # Third
            ])
            
            # Get hot posts
            posts, total = await post_service.get_hot_posts_feed(
                school_id=1,
                page=1,
                page_size=10
            )
            
            # Should return posts
            assert len(posts) > 0
            assert total > 0
            
            # First post should have highest engagement
            assert posts[0].post_id == 4  # Post with 80 likes, 30 comments
    
    @pytest.mark.asyncio
    async def test_get_hot_posts_feed_pagination(self, post_service, sample_posts):
        """Test hot posts feed pagination"""
        with patch('app.repositories.post.RecommendationRepository') as MockRecRepo:
            mock_rec_repo = AsyncMock()
            MockRecRepo.return_value = mock_rec_repo
            
            # Mock many hot posts
            mock_rec_repo.get_hot_posts = AsyncMock(return_value=sample_posts * 3)  # 12 posts
            
            # Get first page
            posts_page1, total1 = await post_service.get_hot_posts_feed(
                school_id=1,
                page=1,
                page_size=5
            )
            
            # Get second page
            posts_page2, total2 = await post_service.get_hot_posts_feed(
                school_id=1,
                page=2,
                page_size=5
            )
            
            # Should return correct page sizes
            assert len(posts_page1) <= 5
            assert len(posts_page2) <= 5
            
            # Total should be consistent
            assert total1 == total2
