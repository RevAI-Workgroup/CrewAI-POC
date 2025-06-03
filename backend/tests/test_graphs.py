"""
Tests for graphs router endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from models.base import Base
from models.user import User
from models.graph import Graph
from utils.dependencies import get_db
from utils.auth import create_access_token, generate_passphrase

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """Create a test user."""
    db = TestingSessionLocal()
    try:
        user = User(
            id="test-user-id",
            pseudo="testuser",
            passphrase=generate_passphrase()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for test user."""
    token = create_access_token(data={"sub": test_user.id, "pseudo": test_user.pseudo})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_graph(test_user):
    """Create a sample graph for testing."""
    db = TestingSessionLocal()
    try:
        graph = Graph(
            id="test-graph-id",
            name="Test Graph",
            description="A test graph",
            graph_data={"nodes": [], "edges": []},
            metadata={"version": "1.0"},
            created_by=test_user.id
        )
        db.add(graph)
        db.commit()
        db.refresh(graph)
        return graph
    finally:
        db.close()


class TestNodeDefinitionsEndpoint:
    """Test node definitions structure endpoint."""
    
    def test_get_node_definitions_structure_success(self, auth_headers):
        """Test successful retrieval of node definitions structure."""
        response = client.get("/api/graph-nodes", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        
        structure = data["data"]
        assert "categories" in structure
        assert "node_types" in structure
        assert "connection_constraints" in structure
        assert "enums" in structure
        
    def test_get_node_definitions_structure_unauthorized(self):
        """Test unauthorized access to node definitions structure."""
        response = client.get("/api/graph-nodes")
        
        assert response.status_code == 401
        
    def test_node_definitions_structure_content(self, auth_headers):
        """Test that node definitions structure contains expected content."""
        response = client.get("/api/graph-nodes", headers=auth_headers)
        
        assert response.status_code == 200
        structure = response.json()["data"]
        
        # Check node types
        node_types = structure["node_types"]
        expected_types = ["crew", "agent", "task", "llm", "tool", "flow"]
        for node_type in expected_types:
            assert node_type in node_types
            
        # Check specific node structure
        crew_def = node_types["crew"]
        assert crew_def["name"] == "Crew"
        assert "fields" in crew_def
        assert "name" in crew_def["fields"]
        assert "agent_ids" in crew_def["fields"]


class TestGraphsCRUDEndpoints:
    """Test graphs CRUD endpoints."""
    
    def test_list_graphs_success(self, auth_headers, sample_graph):
        """Test successful listing of user graphs."""
        response = client.get("/api/graphs", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "count" in data
        assert data["count"] >= 1
        
    def test_list_graphs_unauthorized(self):
        """Test unauthorized access to graphs list."""
        response = client.get("/api/graphs")
        
        assert response.status_code == 401
        
    def test_get_graph_success(self, auth_headers, sample_graph):
        """Test successful retrieval of specific graph."""
        response = client.get(f"/api/graphs/{sample_graph.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        graph_data = data["data"]
        assert graph_data["id"] == sample_graph.id
        assert graph_data["name"] == sample_graph.name
        
    def test_get_graph_not_found(self, auth_headers):
        """Test retrieval of non-existent graph."""
        response = client.get("/api/graphs/non-existent-id", headers=auth_headers)
        
        assert response.status_code == 404
        
    def test_create_graph_success(self, auth_headers):
        """Test successful graph creation."""
        graph_data = {
            "name": "New Test Graph",
            "description": "A newly created test graph",
            "graph_data": {"nodes": [], "edges": []},
            "metadata": {"version": "1.0"}
        }
        
        response = client.post("/api/graphs", json=graph_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        created_graph = data["data"]
        assert created_graph["name"] == graph_data["name"]
        assert created_graph["description"] == graph_data["description"]
        
    def test_create_graph_unauthorized(self):
        """Test unauthorized graph creation."""
        graph_data = {"name": "Unauthorized Graph"}
        
        response = client.post("/api/graphs", json=graph_data)
        
        assert response.status_code == 401
        
    def test_update_graph_success(self, auth_headers, sample_graph):
        """Test successful graph update."""
        update_data = {
            "name": "Updated Graph Name",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/graphs/{sample_graph.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        updated_graph = data["data"]
        assert updated_graph["name"] == update_data["name"]
        assert updated_graph["description"] == update_data["description"]
        
    def test_update_graph_not_found(self, auth_headers):
        """Test update of non-existent graph."""
        update_data = {"name": "Updated Name"}
        
        response = client.put("/api/graphs/non-existent-id", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
        
    def test_delete_graph_success(self, auth_headers, sample_graph):
        """Test successful graph deletion."""
        response = client.delete(f"/api/graphs/{sample_graph.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "message" in data
        
        # Verify graph is deleted
        get_response = client.get(f"/api/graphs/{sample_graph.id}", headers=auth_headers)
        assert get_response.status_code == 404
        
    def test_delete_graph_not_found(self, auth_headers):
        """Test deletion of non-existent graph."""
        response = client.delete("/api/graphs/non-existent-id", headers=auth_headers)
        
        assert response.status_code == 404
        
    def test_graphs_pagination(self, auth_headers, test_user):
        """Test graphs pagination functionality."""
        # Create multiple graphs
        db = TestingSessionLocal()
        try:
            for i in range(5):
                graph = Graph(
                    id=f"test-graph-{i}",
                    name=f"Test Graph {i}",
                    description=f"Test graph number {i}",
                    graph_data={"nodes": [], "edges": []},
                    created_by=test_user.id
                )
                db.add(graph)
            db.commit()
        finally:
            db.close()
            
        # Test pagination
        response = client.get("/api/graphs?skip=0&limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] <= 3
        
        response = client.get("/api/graphs?skip=3&limit=3", headers=auth_headers)
        assert response.status_code == 200 