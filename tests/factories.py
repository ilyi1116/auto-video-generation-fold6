"""
Advanced Test Data Factories
企業級測試數據工廠 - 使用Factory Boy實現可重用、靈活的測試數據生成
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import factory
from faker import Faker

fake = Faker(['en_US', 'zh_TW'])


class BaseFactory(factory.Factory):
    """Base factory with common configurations"""
    
    class Meta:
        abstract = True
    
    # Common test metadata
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class UserFactory(BaseFactory):
    """Factory for creating test users"""
    
    class Meta:
        model = dict
    
    # Basic user information
    id = factory.Sequence(lambda n: n)
    email = factory.LazyAttribute(lambda obj: fake.email())
    username = factory.LazyAttribute(lambda obj: fake.user_name())
    full_name = factory.LazyAttribute(lambda obj: fake.name())
    
    # Authentication
    password_hash = factory.LazyFunction(
        lambda: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeYK2Cj2z1n1J1J1J"  # bcrypt hash of "password123"
    )
    is_active = True
    is_verified = True
    
    # Subscription and limits
    subscription_tier = factory.fuzzy.FuzzyChoice(['free', 'standard', 'professional', 'enterprise'])
    videos_generated = factory.fuzzy.FuzzyInteger(0, 100)
    storage_used_mb = factory.fuzzy.FuzzyInteger(0, 10000)
    api_calls_this_month = factory.fuzzy.FuzzyInteger(0, 1000)
    
    # Profile information
    avatar_url = factory.LazyFunction(lambda: fake.image_url())
    bio = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=200))
    timezone = factory.fuzzy.FuzzyChoice(['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo', 'Asia/Taipei'])
    language = factory.fuzzy.FuzzyChoice(['en', 'zh-TW', 'zh-CN', 'ja', 'es'])
    
    # Account settings
    notification_preferences = factory.LazyFunction(
        lambda: {
            'email_notifications': random.choice([True, False]),
            'sms_notifications': random.choice([True, False]),
            'marketing_emails': random.choice([True, False]),
        }
    )
    
    # Timestamps
    last_login_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-30d', end_date='now')
    )
    
    @factory.post_generation
    def set_subscription_limits(obj, create, extracted, **kwargs):
        """Set subscription limits based on tier"""
        limits = {
            'free': {'videos_per_month': 3, 'storage_gb': 1, 'api_calls_per_month': 100},
            'standard': {'videos_per_month': 50, 'storage_gb': 10, 'api_calls_per_month': 1000},
            'professional': {'videos_per_month': 200, 'storage_gb': 50, 'api_calls_per_month': 5000},
            'enterprise': {'videos_per_month': -1, 'storage_gb': 500, 'api_calls_per_month': 50000},
        }
        obj['subscription_limits'] = limits.get(obj['subscription_tier'], limits['free'])


class VideoProjectFactory(BaseFactory):
    """Factory for creating test video projects"""
    
    class Meta:
        model = dict
    
    # Basic project information
    id = factory.Sequence(lambda n: f"proj_{n:06d}")
    user_id = factory.SubFactory(UserFactory)
    title = factory.LazyAttribute(lambda obj: fake.sentence(nb_words=4))
    description = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=500))
    
    # Content specifications
    theme = factory.fuzzy.FuzzyChoice([
        'technology', 'business', 'education', 'entertainment', 'lifestyle',
        'health', 'finance', 'travel', 'food', 'sports', 'music', 'art'
    ])
    style = factory.fuzzy.FuzzyChoice([
        'modern', 'classic', 'minimalist', 'bold', 'elegant', 'playful',
        'professional', 'creative', 'casual', 'formal'
    ])
    tone = factory.fuzzy.FuzzyChoice([
        'friendly', 'professional', 'enthusiastic', 'calm', 'authoritative',
        'conversational', 'inspiring', 'informative'
    ])
    
    # Technical specifications
    duration_seconds = factory.fuzzy.FuzzyInteger(15, 300)  # 15 seconds to 5 minutes
    aspect_ratio = factory.fuzzy.FuzzyChoice(['16:9', '9:16', '1:1', '4:3'])
    resolution = factory.fuzzy.FuzzyChoice(['720p', '1080p', '4K'])
    frame_rate = factory.fuzzy.FuzzyChoice([24, 30, 60])
    
    # Audio settings
    voice_type = factory.fuzzy.FuzzyChoice([
        'professional_male', 'professional_female', 'casual_male', 'casual_female',
        'narrator_male', 'narrator_female', 'energetic_male', 'energetic_female'
    ])
    music_genre = factory.fuzzy.FuzzyChoice([
        'ambient', 'corporate', 'upbeat', 'dramatic', 'peaceful',
        'electronic', 'acoustic', 'cinematic', 'none'
    ])
    include_captions = factory.fuzzy.FuzzyChoice([True, False])
    
    # Platform settings
    target_platforms = factory.LazyFunction(
        lambda: random.sample(['youtube', 'tiktok', 'instagram', 'facebook', 'twitter', 'linkedin'], 
                            random.randint(1, 3))
    )
    
    # Project status
    status = factory.fuzzy.FuzzyChoice([
        'draft', 'generating', 'completed', 'failed', 'cancelled'
    ])
    progress_percentage = factory.LazyAttribute(
        lambda obj: 100 if obj['status'] == 'completed' else random.randint(0, 99)
    )
    
    # Content data
    script_content = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=2000))
    scenes = factory.LazyFunction(
        lambda: [
            {
                'id': i,
                'visual_description': fake.sentence(nb_words=10),
                'narration': fake.sentence(nb_words=15),
                'duration': random.randint(3, 10),
                'image_url': fake.image_url(),
            }
            for i in range(random.randint(3, 8))
        ]
    )
    
    # Output files
    video_url = factory.LazyFunction(lambda: fake.url() + '/video.mp4')
    thumbnail_url = factory.LazyFunction(lambda: fake.image_url())
    preview_url = factory.LazyFunction(lambda: fake.url() + '/preview.mp4')
    
    # Metadata
    file_size_mb = factory.fuzzy.FuzzyInteger(5, 200)
    processing_time_seconds = factory.fuzzy.FuzzyInteger(30, 600)
    cost_credits = factory.fuzzy.FuzzyInteger(1, 10)
    
    # Analytics
    view_count = factory.fuzzy.FuzzyInteger(0, 10000)
    download_count = factory.fuzzy.FuzzyInteger(0, 100)
    share_count = factory.fuzzy.FuzzyInteger(0, 50)


class AIServiceResponseFactory(BaseFactory):
    """Factory for creating mock AI service responses"""
    
    class Meta:
        model = dict
    
    # Response metadata
    request_id = factory.LazyFunction(lambda: fake.uuid4())
    service_name = factory.fuzzy.FuzzyChoice(['gemini', 'openai', 'stability', 'elevenlabs'])
    timestamp = factory.LazyFunction(datetime.utcnow)
    processing_time_ms = factory.fuzzy.FuzzyInteger(100, 5000)
    
    # Response status
    status = factory.fuzzy.FuzzyChoice(['success', 'error', 'timeout'])
    error_message = factory.Maybe(
        'status',
        yes_declaration=None,
        no_declaration=factory.LazyFunction(lambda: fake.sentence())
    )
    
    # Content (varies by service)
    content = factory.LazyFunction(
        lambda: {
            'text': fake.text(max_nb_chars=1000),
            'confidence': random.uniform(0.7, 1.0),
            'tokens_used': random.randint(50, 500),
        }
    )


class ErrorLogFactory(BaseFactory):
    """Factory for creating test error logs"""
    
    class Meta:
        model = dict
    
    # Error identification
    id = factory.Sequence(lambda n: f"err_{n:08d}")
    error_code = factory.fuzzy.FuzzyChoice([
        'AUTH_001', 'VIDEO_002', 'AI_003', 'STORAGE_004', 'NETWORK_005',
        'VALIDATION_006', 'RATE_LIMIT_007', 'QUOTA_008', 'PROCESSING_009'
    ])
    severity = factory.fuzzy.FuzzyChoice(['low', 'medium', 'high', 'critical'])
    
    # Error details
    message = factory.LazyAttribute(lambda obj: fake.sentence())
    stack_trace = factory.LazyFunction(lambda: fake.text(max_nb_chars=2000))
    context = factory.LazyFunction(
        lambda: {
            'user_id': random.randint(1, 1000),
            'request_id': fake.uuid4(),
            'endpoint': fake.uri_path(),
            'method': random.choice(['GET', 'POST', 'PUT', 'DELETE']),
            'ip_address': fake.ipv4(),
            'user_agent': fake.user_agent(),
        }
    )
    
    # System information
    service_name = factory.fuzzy.FuzzyChoice([
        'api-gateway', 'auth-service', 'video-service', 'ai-service', 'storage-service'
    ])
    instance_id = factory.LazyFunction(lambda: fake.uuid4()[:8])
    
    # Resolution status
    resolved = factory.fuzzy.FuzzyChoice([True, False])
    resolution_notes = factory.Maybe(
        'resolved',
        yes_declaration=factory.LazyFunction(lambda: fake.text(max_nb_chars=200)),
        no_declaration=None
    )


class PerformanceMetricFactory(BaseFactory):
    """Factory for creating performance metrics"""
    
    class Meta:
        model = dict
    
    # Metric identification
    metric_name = factory.fuzzy.FuzzyChoice([
        'response_time', 'throughput', 'error_rate', 'cpu_usage', 'memory_usage',
        'disk_io', 'network_io', 'queue_length', 'active_connections'
    ])
    service_name = factory.fuzzy.FuzzyChoice([
        'api-gateway', 'auth-service', 'video-service', 'ai-service', 'storage-service'
    ])
    
    # Metric values
    value = factory.fuzzy.FuzzyFloat(0.0, 100.0)
    unit = factory.LazyAttribute(lambda obj: {
        'response_time': 'ms',
        'throughput': 'req/s',
        'error_rate': '%',
        'cpu_usage': '%',
        'memory_usage': '%',
        'disk_io': 'MB/s',
        'network_io': 'KB/s',
        'queue_length': 'count',
        'active_connections': 'count',
    }.get(obj['metric_name'], 'count'))
    
    # Timestamps
    timestamp = factory.LazyFunction(datetime.utcnow)
    
    # Additional metadata
    tags = factory.LazyFunction(
        lambda: {
            'environment': random.choice(['development', 'staging', 'production']),
            'region': random.choice(['us-east-1', 'us-west-2', 'eu-west-1']),
            'instance_type': random.choice(['t3.micro', 't3.small', 't3.medium']),
        }
    )


class TestDataManager:
    """Centralized test data management"""
    
    def __init__(self):
        self._created_objects = []
        self._cleanup_functions = []
    
    def create_user(self, **kwargs) -> Dict[str, Any]:
        """Create a test user with cleanup tracking"""
        user = UserFactory(**kwargs)
        self._created_objects.append(('user', user['id']))
        return user
    
    def create_video_project(self, user_id: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Create a test video project"""
        if user_id is None:
            user = self.create_user()
            user_id = user['id']
        
        project = VideoProjectFactory(user_id=user_id, **kwargs)
        self._created_objects.append(('video_project', project['id']))
        return project
    
    def create_error_log(self, **kwargs) -> Dict[str, Any]:
        """Create a test error log"""
        error = ErrorLogFactory(**kwargs)
        self._created_objects.append(('error_log', error['id']))
        return error
    
    def create_performance_metric(self, **kwargs) -> Dict[str, Any]:
        """Create a test performance metric"""
        metric = PerformanceMetricFactory(**kwargs)
        self._created_objects.append(('performance_metric', metric))
        return metric
    
    def create_batch_users(self, count: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple test users efficiently"""
        users = [UserFactory(**kwargs) for _ in range(count)]
        for user in users:
            self._created_objects.append(('user', user['id']))
        return users
    
    def create_complete_project_scenario(self) -> Dict[str, Any]:
        """Create a complete project scenario with user, project, and related data"""
        user = self.create_user(subscription_tier='professional')
        project = self.create_video_project(user_id=user['id'], status='completed')
        
        # Add some metrics and logs
        metrics = [
            self.create_performance_metric(service_name='video-service')
            for _ in range(5)
        ]
        
        error_log = self.create_error_log(
            severity='low',
            service_name='video-service',
            resolved=True
        )
        
        return {
            'user': user,
            'project': project,
            'metrics': metrics,
            'error_log': error_log,
        }
    
    def register_cleanup(self, cleanup_function):
        """Register a cleanup function"""
        self._cleanup_functions.append(cleanup_function)
    
    async def cleanup_all(self):
        """Clean up all created test data"""
        # Run cleanup functions
        for cleanup_func in reversed(self._cleanup_functions):
            try:
                if callable(cleanup_func):
                    await cleanup_func()
            except Exception as e:
                print(f"Cleanup function failed: {e}")
        
        # Clear tracking
        self._created_objects.clear()
        self._cleanup_functions.clear()
    
    def get_created_objects(self) -> List[tuple]:
        """Get list of created objects for verification"""
        return self._created_objects.copy()


# Global test data manager instance
test_data_manager = TestDataManager()


# Pytest fixtures
import pytest


@pytest.fixture
def user_factory():
    """User factory fixture"""
    return UserFactory


@pytest.fixture  
def video_project_factory():
    """Video project factory fixture"""
    return VideoProjectFactory


@pytest.fixture
def ai_response_factory():
    """AI service response factory fixture"""
    return AIServiceResponseFactory


@pytest.fixture
def error_log_factory():
    """Error log factory fixture"""
    return ErrorLogFactory


@pytest.fixture
def performance_metric_factory():
    """Performance metric factory fixture"""
    return PerformanceMetricFactory


@pytest.fixture
def test_data_manager_fixture():
    """Test data manager with automatic cleanup"""
    manager = TestDataManager()
    yield manager
    # Cleanup happens automatically when fixture is torn down


@pytest.fixture
def sample_users():
    """Pre-created sample users for tests"""
    return [
        UserFactory(subscription_tier='free', email='free@test.com'),
        UserFactory(subscription_tier='standard', email='standard@test.com'),
        UserFactory(subscription_tier='professional', email='pro@test.com'),
        UserFactory(subscription_tier='enterprise', email='enterprise@test.com'),
    ]


@pytest.fixture
def complete_project_scenario():
    """Complete project scenario with all related data"""
    return test_data_manager.create_complete_project_scenario()