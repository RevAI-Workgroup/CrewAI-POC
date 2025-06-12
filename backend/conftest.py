"""
Shared pytest configuration and fixtures for the backend test suite.
Provides optimized test database setup, async test configuration, and common fixtures.
"""

import asyncio
import os
import pytest
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test environment variables before importing app modules
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-chars-long!")

from main import app
from db_config import Base, get_db


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require database/redis)"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests (slow)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow tests"
    )
    config.addinivalue_line(
        "markers", "asyncio: marks tests as async tests"
    )
    config.addinivalue_line(
        "markers", "websocket: marks tests as websocket tests"
    )
    config.addinivalue_line(
        "markers", "sse: marks tests as server-sent events tests"
    )


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test database fixtures
@pytest.fixture(scope="session")
def test_db_file() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    yield db_path
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="session")
def test_engine(test_db_file: str):
    """Create a test database engine."""
    database_url = f"sqlite:///{test_db_file}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        echo=False,  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()


@pytest.fixture(scope="session")
def test_async_engine(test_db_file: str):
    """Create a test async database engine."""
    database_url = f"sqlite+aiosqlite:///{test_db_file}"
    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
    )
    
    yield engine
    
    # Cleanup
    engine.sync_engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    
    # Create session bound to connection
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
async def async_db_session(test_async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for each test."""
    async with test_async_engine.connect() as connection:
        async with connection.begin() as transaction:
            # Create async session bound to connection  
            session = AsyncSession(bind=connection, expire_on_commit=False)
            try:
                yield session
            finally:
                await session.close()
                await transaction.rollback()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear overrides
    app.dependency_overrides.clear()


# Mock fixtures for external services
@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock = MagicMock()
    mock.get = MagicMock(return_value=None)
    mock.set = MagicMock(return_value=True)
    mock.delete = MagicMock(return_value=1)
    mock.exists = MagicMock(return_value=False)
    mock.ping = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_celery():
    """Mock Celery app for testing."""
    mock = MagicMock()
    mock.send_task = MagicMock(return_value=MagicMock(id="test-task-id"))
    return mock


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing."""
    mock = AsyncMock()
    mock.accept = AsyncMock()
    mock.send_text = AsyncMock()
    mock.send_json = AsyncMock()
    mock.close = AsyncMock()
    return mock


# Performance testing fixtures
@pytest.fixture
def benchmark_config():
    """Configuration for performance benchmarks."""
    return {
        "min_rounds": 3,
        "max_time": 1.0,
        "warmup": True,
        "warmup_iterations": 1,
    }


# Test data factories
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "is_active": True,
    }


@pytest.fixture
def sample_graph_data():
    """Sample graph data for testing."""
    return {
        "name": "Test Graph",
        "description": "A test graph for unit testing",
        "nodes": [],
        "edges": [],
    }


@pytest.fixture
def sample_execution_data():
    """Sample execution data for testing."""
    return {
        "graph_id": 1,
        "status": "pending",
        "metadata": {},
    }


# Skip markers for integration tests
@pytest.fixture(autouse=True)
def skip_integration_tests(request):
    """Skip integration tests if external services are not available."""
    if request.node.get_closest_marker("integration"):
        # Check if required services are available
        database_url = os.getenv("DATABASE_URL")
        redis_url = os.getenv("REDIS_URL")
        
        if not database_url or not redis_url:
            pytest.skip("Integration test requires database and redis setup")


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_test_data(db_session):
    """Cleanup test data after each test."""
    yield
    
    # Clean up any test data
    try:
        # Clear all tables (in reverse order of dependencies)
        for table in reversed(Base.metadata.sorted_tables):
            db_session.execute(text(f"DELETE FROM {table.name}"))
        db_session.commit()
    except Exception:
        db_session.rollback() 