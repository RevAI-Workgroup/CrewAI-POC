"""
Integration tests for Thread Router endpoints
Tests HTTP endpoints, authentication, and request/response handling
"""

import pytest
import uuid
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from main import app
from models.thread import Thread, ThreadStatus
from models.graph import Graph
from models.user import User
from schemas.thread_schemas import ThreadCreateRequest, ThreadUpdateRequest
from services.thread_service import ThreadService
from utils.dependencies import get_current_user
from db_config import get_db


class TestThreadRouter:
    """Test suite for Thread Router endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock user
        self.user_id = str(uuid.uuid4())
        self.mock_user = Mock(spec=User)
        self.mock_user.id = self.user_id
        
        # Mock graph
        self.graph_id = str(uuid.uuid4())
        self.mock_graph = Mock(spec=Graph)
        self.mock_graph.id = self.graph_id
        self.mock_graph.user_id = self.user_id
        
        # Mock thread with proper attributes for serialization
        self.thread_id = str(uuid.uuid4())
        self.mock_thread = Mock(spec=Thread)
        self.mock_thread.id = self.thread_id
        self.mock_thread.graph_id = self.graph_id
        self.mock_thread.name = "Test Thread"
        self.mock_thread.description = "Test Description"
        self.mock_thread.status = ThreadStatus.ACTIVE.value
        self.mock_thread.thread_config = {}
        self.mock_thread.last_activity_at = None
        self.mock_thread.created_at = "2024-01-01T00:00:00"
        self.mock_thread.updated_at = "2024-01-01T00:00:00"
        self.mock_thread.message_count = 0
        
        # Mock database session
        self.mock_db = Mock()
        
        # Override FastAPI dependencies
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: self.mock_db
        
        # Create test client
        self.client = TestClient(app)
    
    def _create_mock_thread(self, **overrides):
        """Helper method to create a properly mocked thread with all required attributes."""
        thread = Mock(spec=Thread)
        thread.id = overrides.get('id', self.thread_id)
        thread.graph_id = overrides.get('graph_id', self.graph_id)
        thread.name = overrides.get('name', "Test Thread")
        thread.description = overrides.get('description', "Test Description")
        thread.status = overrides.get('status', ThreadStatus.ACTIVE.value)
        thread.thread_config = overrides.get('thread_config', {})
        thread.last_activity_at = overrides.get('last_activity_at', None)
        thread.created_at = overrides.get('created_at', "2024-01-01T00:00:00")
        thread.updated_at = overrides.get('updated_at', "2024-01-01T00:00:00")
        thread.message_count = overrides.get('message_count', 0)
        return thread
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clear dependency overrides
        app.dependency_overrides.clear()
    
    def test_create_thread_success(self):
        """Test successful thread creation endpoint."""
        # Arrange
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.create_thread.return_value = self.mock_thread
            
            request_data = {
                "graph_id": self.graph_id,
                "name": "Test Thread",
                "description": "Test Description"
            }
            
            # Act
            response = self.client.post(
                "/api/threads/",
                json=request_data
            )
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            mock_service.create_thread.assert_called_once_with(
                graph_id=self.graph_id,
                user_id=str(self.mock_user.id),
                name="Test Thread",
                description="Test Description",
                thread_config=None
            )
    
    def test_create_thread_validation_error(self):
        """Test thread creation with validation error."""
        # Arrange
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.create_thread.side_effect = ValueError("Invalid graph")
            
            request_data = {
                "graph_id": "invalid_graph_id",
                "name": "Test Thread"
            }
            
            # Act
            response = self.client.post(
                "/api/threads/",
                json=request_data
            )
            
            # Assert
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid graph" in response.json()["detail"]
    
    def test_create_thread_permission_error(self):
        """Test thread creation with permission error."""
        # Arrange
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.create_thread.side_effect = PermissionError("Access denied")
            
            request_data = {
                "graph_id": self.graph_id,
                "name": "Test Thread"
            }
            
            # Act
            response = self.client.post(
                "/api/threads/",
                json=request_data
            )
            
            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Access denied" in response.json()["detail"]
    
    def test_get_thread_success(self):
        """Test successful thread retrieval endpoint."""
        # Arrange
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.get_thread.return_value = self.mock_thread
            
            # Act
            response = self.client.get(f"/api/threads/{self.thread_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            mock_service.get_thread.assert_called_once_with(self.thread_id, str(self.mock_user.id))
    
    def test_get_thread_not_found(self):
        """Test thread retrieval when thread not found."""
        # Arrange
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.get_thread.return_value = None
            
            # Act
            response = self.client.get(f"/api/threads/{self.thread_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Thread not found" in response.json()["detail"]
    
    def test_get_graph_threads_success(self):
        """Test successful graph threads retrieval."""
        # Arrange
        threads = [self.mock_thread]
        
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.get_graph_threads.return_value = threads
            
            # Act
            response = self.client.get(f"/api/threads/graph/{self.graph_id}")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert response_data["total"] == 1
            assert response_data["graph_id"] == self.graph_id
            assert len(response_data["threads"]) == 1
    
    def test_update_thread_success(self):
        """Test successful thread update."""
        # Arrange
        updated_thread = self._create_mock_thread(
            name="Updated Thread",
            description="Updated Description"
        )
        
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.update_thread.return_value = updated_thread
            
            request_data = {
                "name": "Updated Thread",
                "description": "Updated Description"
            }
            
            # Act
            response = self.client.put(
                f"/api/threads/{self.thread_id}",
                json=request_data
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            mock_service.update_thread.assert_called_once()
    
    def test_delete_thread_success(self):
        """Test successful thread deletion."""
        # Arrange
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.delete_thread.return_value = True
            
            # Act
            response = self.client.delete(f"/api/threads/{self.thread_id}")
            
            # Assert
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_service.delete_thread.assert_called_once_with(self.thread_id, str(self.mock_user.id))
    
    def test_delete_thread_not_found(self):
        """Test thread deletion when thread not found."""
        # Arrange
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.delete_thread.return_value = False
            
            # Act
            response = self.client.delete(f"/api/threads/{self.thread_id}")
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Thread not found" in response.json()["detail"]
    
    def test_list_user_threads_success(self):
        """Test successful user threads listing."""
        # Arrange
        threads = [self.mock_thread]
        
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.list_user_threads.return_value = threads
            
            # Act
            response = self.client.get("/api/threads/?limit=10&offset=0")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            assert len(response.json()) == 1
            mock_service.list_user_threads.assert_called_once()
    
    def test_archive_thread_success(self):
        """Test successful thread archiving."""
        # Arrange
        archived_thread = self._create_mock_thread(status=ThreadStatus.ARCHIVED.value)
        
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.archive_thread.return_value = archived_thread
            
            # Act
            response = self.client.post(f"/api/threads/{self.thread_id}/archive")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            mock_service.archive_thread.assert_called_once_with(self.thread_id, str(self.mock_user.id))
    
    def test_activate_thread_success(self):
        """Test successful thread activation."""
        # Arrange
        activated_thread = self._create_mock_thread(status=ThreadStatus.ACTIVE.value)
        
        with patch('routers.threads.ThreadService') as mock_service_class:
            mock_service = Mock(spec=ThreadService)
            mock_service_class.return_value = mock_service
            mock_service.activate_thread.return_value = activated_thread
            
            # Act
            response = self.client.post(f"/api/threads/{self.thread_id}/activate")
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            mock_service.activate_thread.assert_called_once_with(self.thread_id, str(self.mock_user.id))
    
    def test_unauthorized_access(self):
        """Test endpoints without authentication."""
        # Clear the dependency override for this test
        app.dependency_overrides.clear()
        
        # Act
        response = self.client.get(f"/api/threads/{self.thread_id}")
        
        # Assert
        # Note: FastAPI returns 403 when dependency overrides are cleared 
        # rather than 401, because the dependency injection system 
        # sees it as a "forbidden" rather than "unauthorized" case
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Restore dependency override for other tests
        app.dependency_overrides[get_current_user] = lambda: self.mock_user
        app.dependency_overrides[get_db] = lambda: self.mock_db
    
    def test_invalid_json_request(self):
        """Test endpoints with invalid JSON."""
        # Act
        response = self.client.post(
            "/api/threads/",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 