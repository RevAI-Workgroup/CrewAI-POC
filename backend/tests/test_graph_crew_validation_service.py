import pytest
import uuid
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from services.graph_crew_validation_service import GraphCrewValidationService
from models.graph import Graph
from models.node_types import NodeTypeEnum


class TestGraphCrewValidationService:
    """Test suite for GraphCrewValidationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db_mock = Mock(spec=Session)
        self.service = GraphCrewValidationService(self.db_mock)
    
    def create_mock_graph(self, graph_data=None):
        """Create a mock graph for testing."""
        graph = Mock(spec=Graph)
        graph.id = str(uuid.uuid4())
        graph.graph_data = graph_data
        return graph
    
    def test_validate_graph_for_chat_success(self):
        """Test successful validation of a graph with single crew."""
        # Arrange
        graph_data = {
            'nodes': [
                {
                    'id': 'crew-1',
                    'type': NodeTypeEnum.CREW.value,
                    'data': {
                        'agent_ids': ['agent-1'],
                        'task_ids': ['task-1']
                    }
                },
                {
                    'id': 'agent-1',
                    'type': NodeTypeEnum.AGENT.value,
                    'data': {'role': 'Test Agent'}
                },
                {
                    'id': 'task-1',
                    'type': NodeTypeEnum.TASK.value,
                    'data': {'description': 'Test Task'}
                }
            ],
            'edges': []
        }
        
        graph = self.create_mock_graph(graph_data)
        
        # Act
        result = self.service.validate_graph_for_chat(graph)
        
        # Assert
        assert result['is_valid'] is True
        assert result['crew_node_id'] == 'crew-1'
        assert result['agent_count'] == 1
        assert result['task_count'] == 1
        assert len(result['errors']) == 0
    
    def test_validate_graph_no_data(self):
        """Test validation fails when graph has no data."""
        # Arrange
        graph = self.create_mock_graph(None)
        
        # Act
        result = self.service.validate_graph_for_chat(graph)
        
        # Assert
        assert result['is_valid'] is False
        assert 'Graph has no data' in result['errors']
    
    def test_validate_graph_no_nodes(self):
        """Test validation fails when graph has no nodes."""
        # Arrange
        graph_data = {'nodes': [], 'edges': []}
        graph = self.create_mock_graph(graph_data)
        
        # Act
        result = self.service.validate_graph_for_chat(graph)
        
        # Assert
        assert result['is_valid'] is False
        assert 'Graph has no nodes' in result['errors']
    
    def test_validate_graph_no_crew_nodes(self):
        """Test validation fails when graph has no crew nodes."""
        # Arrange
        graph_data = {
            'nodes': [
                {
                    'id': 'agent-1',
                    'type': NodeTypeEnum.AGENT.value,
                    'data': {'role': 'Test Agent'}
                }
            ],
            'edges': []
        }
        graph = self.create_mock_graph(graph_data)
        
        # Act
        result = self.service.validate_graph_for_chat(graph)
        
        # Assert
        assert result['is_valid'] is False
        assert 'must have at least one crew node' in result['errors'][0]
    
    def test_validate_graph_multiple_crew_nodes(self):
        """Test validation fails when graph has multiple crew nodes."""
        # Arrange
        graph_data = {
            'nodes': [
                {
                    'id': 'crew-1',
                    'type': NodeTypeEnum.CREW.value,
                    'data': {'agent_ids': [], 'task_ids': []}
                },
                {
                    'id': 'crew-2',
                    'type': NodeTypeEnum.CREW.value,
                    'data': {'agent_ids': [], 'task_ids': []}
                }
            ],
            'edges': []
        }
        graph = self.create_mock_graph(graph_data)
        
        # Act
        result = self.service.validate_graph_for_chat(graph)
        
        # Assert
        assert result['is_valid'] is False
        assert 'can only have one crew node' in result['errors'][0]
        assert 'found 2 crew nodes' in result['errors'][0]
    
    def test_validate_graph_crew_no_id(self):
        """Test validation fails when crew node has no id."""
        # Arrange
        graph_data = {
            'nodes': [
                {
                    'type': NodeTypeEnum.CREW.value,
                    'data': {'agent_ids': [], 'task_ids': []}
                }
            ],
            'edges': []
        }
        graph = self.create_mock_graph(graph_data)
        
        # Act
        result = self.service.validate_graph_for_chat(graph)
        
        # Assert
        assert result['is_valid'] is False
        assert 'Crew node must have an id' in result['errors']
    
    def test_validate_graph_missing_referenced_agents(self):
        """Test validation fails when crew references non-existent agents."""
        # Arrange
        graph_data = {
            'nodes': [
                {
                    'id': 'crew-1',
                    'type': NodeTypeEnum.CREW.value,
                    'data': {
                        'agent_ids': ['agent-1', 'agent-missing'],
                        'task_ids': []
                    }
                },
                {
                    'id': 'agent-1',
                    'type': NodeTypeEnum.AGENT.value,
                    'data': {'role': 'Test Agent'}
                }
            ],
            'edges': []
        }
        graph = self.create_mock_graph(graph_data)
        
        # Act
        result = self.service.validate_graph_for_chat(graph)
        
        # Assert
        assert result['is_valid'] is False
        assert 'non-existent agent nodes' in result['errors'][0]
        assert 'agent-missing' in result['errors'][0]
    
    def test_validate_single_crew_restriction_raises_on_invalid(self):
        """Test that validate_single_crew_restriction raises exception on invalid graph."""
        # Arrange
        graph = self.create_mock_graph({'nodes': [], 'edges': []})
        
        # Act & Assert
        with pytest.raises(ValueError, match="Graph validation failed"):
            self.service.validate_single_crew_restriction(graph)
    
    def test_validate_single_crew_restriction_passes_on_valid(self):
        """Test that validate_single_crew_restriction passes on valid graph."""
        # Arrange
        graph_data = {
            'nodes': [
                {
                    'id': 'crew-1',
                    'type': NodeTypeEnum.CREW.value,
                    'data': {'agent_ids': ['agent-1'], 'task_ids': ['task-1']}
                },
                {
                    'id': 'agent-1',
                    'type': NodeTypeEnum.AGENT.value,
                    'data': {'role': 'Test Agent'}
                },
                {
                    'id': 'task-1',
                    'type': NodeTypeEnum.TASK.value,
                    'data': {'description': 'Test Task'}
                }
            ],
            'edges': []
        }
        graph = self.create_mock_graph(graph_data)
        
        # Act - should not raise exception
        self.service.validate_single_crew_restriction(graph)
    
    def test_get_crew_node_from_graph(self):
        """Test getting crew node from a valid graph."""
        # Arrange
        crew_node = {
            'id': 'crew-1',
            'type': NodeTypeEnum.CREW.value,
            'data': {'agent_ids': ['agent-1'], 'task_ids': ['task-1']}
        }
        graph_data = {
            'nodes': [
                crew_node,
                {
                    'id': 'agent-1',
                    'type': NodeTypeEnum.AGENT.value,
                    'data': {'role': 'Test Agent'}
                },
                {
                    'id': 'task-1',
                    'type': NodeTypeEnum.TASK.value,
                    'data': {'description': 'Test Task'}
                }
            ],
            'edges': []
        }
        graph = self.create_mock_graph(graph_data)
        
        # Act
        result = self.service.get_crew_node_from_graph(graph)
        
        # Assert
        assert result == crew_node
    
    def test_get_crew_node_from_invalid_graph(self):
        """Test getting crew node from invalid graph returns None."""
        # Arrange
        graph = self.create_mock_graph({'nodes': [], 'edges': []})
        
        # Act
        result = self.service.get_crew_node_from_graph(graph)
        
        # Assert
        assert result is None 