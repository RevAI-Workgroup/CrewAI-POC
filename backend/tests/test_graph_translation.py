"""
Unit tests for Graph Translation Service

Tests the conversion of graph data from JSON format to CrewAI objects.
"""

import pytest
from unittest.mock import Mock, MagicMock
from crewai import Agent, Task, Crew, Process

from ..services.graph_translation import GraphTranslationService, GraphTranslationError, GraphDataExtractor
from ..models.graph import Graph


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def translation_service(mock_db):
    """Graph translation service instance."""
    return GraphTranslationService(mock_db)


@pytest.fixture
def simple_graph_data():
    """Simple valid graph data."""
    return {
        "nodes": [
            {
                "id": "agent1",
                "type": "agent",
                "data": {
                    "role": "Research Analyst",
                    "goal": "Analyze data and provide insights",
                    "backstory": "You are an experienced analyst with 5+ years in data analysis"
                }
            },
            {
                "id": "task1", 
                "type": "task",
                "data": {
                    "description": "Analyze quarterly sales data",
                    "expected_output": "Comprehensive sales analysis report with recommendations",
                    "agent_id": "agent1"
                }
            }
        ],
        "edges": [
            {
                "id": "edge1",
                "source": "agent1",
                "target": "task1",
                "type": "assignment"
            }
        ],
        "metadata": {
            "process": "sequential",
            "verbose": True
        }
    }


@pytest.fixture
def complex_graph_data():
    """Complex graph with multiple agents, tasks, and dependencies."""
    return {
        "nodes": [
            {
                "id": "researcher",
                "type": "agent",
                "data": {
                    "role": "Senior Researcher",
                    "goal": "Conduct comprehensive research",
                    "backstory": "Expert researcher with domain knowledge"
                }
            },
            {
                "id": "writer",
                "type": "agent", 
                "data": {
                    "role": "Content Writer",
                    "goal": "Create compelling content",
                    "backstory": "Experienced writer with excellent communication skills"
                }
            },
            {
                "id": "research_task",
                "type": "task",
                "data": {
                    "description": "Research the topic thoroughly",
                    "expected_output": "Detailed research findings and sources"
                }
            },
            {
                "id": "writing_task",
                "type": "task",
                "data": {
                    "description": "Write content based on research",
                    "expected_output": "Well-written article or report"
                }
            }
        ],
        "edges": [
            {
                "id": "edge1",
                "source": "researcher",
                "target": "research_task",
                "type": "assignment"
            },
            {
                "id": "edge2", 
                "source": "writer",
                "target": "writing_task",
                "type": "assignment"
            },
            {
                "id": "edge3",
                "source": "research_task",
                "target": "writing_task", 
                "type": "dependency"
            }
        ],
        "metadata": {
            "process": "sequential"
        }
    }


@pytest.fixture
def mock_graph(simple_graph_data):
    """Mock Graph model instance."""
    graph = Mock(spec=Graph)
    graph.id = "test-graph-123"
    graph.graph_data = simple_graph_data
    return graph


class TestGraphTranslationService:
    """Test cases for GraphTranslationService."""
    
    def test_translate_simple_graph(self, translation_service, mock_graph):
        """Test translation of a simple graph with one agent and one task."""
        crew = translation_service.translate_graph(mock_graph)
        
        assert isinstance(crew, Crew)
        assert len(crew.agents) == 1
        assert len(crew.tasks) == 1
        assert crew.process == Process.sequential
        
        # Check agent properties
        agent = crew.agents[0]
        assert isinstance(agent, Agent)
        assert agent.role == "Research Analyst"
        assert agent.goal == "Analyze data and provide insights"
        assert "experienced analyst" in agent.backstory.lower()
        
        # Check task properties
        task = crew.tasks[0]
        assert isinstance(task, Task)
        assert "quarterly sales data" in task.description.lower()
        assert "sales analysis report" in task.expected_output.lower()
        assert task.agent == agent
    
    def test_translate_complex_graph(self, translation_service, complex_graph_data):
        """Test translation of a complex graph with dependencies."""
        mock_graph = Mock(spec=Graph)
        mock_graph.id = "complex-graph-456"
        mock_graph.graph_data = complex_graph_data
        
        crew = translation_service.translate_graph(mock_graph)
        
        assert isinstance(crew, Crew)
        assert len(crew.agents) == 2
        assert len(crew.tasks) == 2
        
        # Check that task dependency was established
        writing_task = None
        research_task = None
        
        for task in crew.tasks:
            if "research" in task.description.lower():
                research_task = task
            elif "write" in task.description.lower():
                writing_task = task
        
                assert research_task is not None
        assert writing_task is not None
        assert writing_task.context is not None
        assert research_task in writing_task.context
    
    def test_translate_graph_with_no_data(self, translation_service):
        """Test handling of graph with no graph_data."""
        mock_graph = Mock(spec=Graph)
        mock_graph.id = "empty-graph"
        mock_graph.graph_data = None
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(mock_graph)
        
        assert "no graph_data" in str(exc_info.value)
    
    def test_translate_graph_invalid_structure(self, translation_service):
        """Test handling of invalid graph structure."""
        mock_graph = Mock(spec=Graph)
        mock_graph.id = "invalid-graph"
        mock_graph.graph_data = {"invalid": "structure"}
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(mock_graph)
        
        assert "must contain 'nodes'" in str(exc_info.value)
    
    def test_translate_graph_missing_agent_fields(self, translation_service):
        """Test handling of agent nodes with missing required fields."""
        invalid_data = {
            "nodes": [
                {
                    "id": "agent1",
                    "type": "agent",
                    "data": {
                        "role": "Analyst"
                        # Missing goal and backstory
                    }
                },
                {
                    "id": "task1",
                    "type": "task", 
                    "data": {
                        "description": "Test task",
                        "expected_output": "Test output"
                    }
                }
            ],
            "edges": []
        }
        
        mock_graph = Mock(spec=Graph)
        mock_graph.id = "invalid-agent-graph"
        mock_graph.graph_data = invalid_data
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(mock_graph)
        
        assert "missing required field" in str(exc_info.value)
    
    def test_translate_graph_missing_task_fields(self, translation_service):
        """Test handling of task nodes with missing required fields."""
        invalid_data = {
            "nodes": [
                {
                    "id": "agent1",
                    "type": "agent",
                    "data": {
                        "role": "Analyst",
                        "goal": "Analyze",
                        "backstory": "Expert analyst"
                    }
                },
                {
                    "id": "task1",
                    "type": "task",
                    "data": {
                        "description": "Test task"
                        # Missing expected_output
                    }
                }
            ],
            "edges": []
        }
        
        mock_graph = Mock(spec=Graph)
        mock_graph.id = "invalid-task-graph"
        mock_graph.graph_data = invalid_data
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(mock_graph)
        
        assert "missing required field" in str(exc_info.value)
    
    def test_translate_graph_no_agents(self, translation_service):
        """Test handling of graph with no agent nodes."""
        invalid_data = {
            "nodes": [
                {
                    "id": "task1",
                    "type": "task",
                    "data": {
                        "description": "Test task",
                        "expected_output": "Test output"
                    }
                }
            ],
            "edges": []
        }
        
        mock_graph = Mock(spec=Graph)
        mock_graph.id = "no-agents-graph"
        mock_graph.graph_data = invalid_data
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(mock_graph)
        
        assert "at least one agent" in str(exc_info.value)
    
    def test_translate_graph_no_tasks(self, translation_service):
        """Test handling of graph with no task nodes."""
        invalid_data = {
            "nodes": [
                {
                    "id": "agent1",
                    "type": "agent",
                    "data": {
                        "role": "Analyst",
                        "goal": "Analyze",
                        "backstory": "Expert analyst"
                    }
                }
            ],
            "edges": []
        }
        
        mock_graph = Mock(spec=Graph)
        mock_graph.id = "no-tasks-graph"
        mock_graph.graph_data = invalid_data
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(mock_graph)
        
        assert "at least one task" in str(exc_info.value)
    
    def test_determine_process_type_sequential(self, translation_service):
        """Test process type determination for sequential process."""
        nodes = []
        metadata = {"process": "sequential"}
        
        process_type = translation_service._determine_process_type(nodes, metadata)
        assert process_type == Process.sequential
    
    def test_determine_process_type_hierarchical(self, translation_service):
        """Test process type determination for hierarchical process."""
        nodes = []
        metadata = {"process": "hierarchical"}
        
        process_type = translation_service._determine_process_type(nodes, metadata)
        assert process_type == Process.hierarchical
    
    def test_determine_process_type_crew_node(self, translation_service):
        """Test process type determination from crew node."""
        nodes = [
            {
                "id": "crew1",
                "type": "crew",
                "data": {"process": "hierarchical"}
            }
        ]
        metadata = {"process": "sequential"}
        
        process_type = translation_service._determine_process_type(nodes, metadata)
        assert process_type == Process.hierarchical


class TestGraphDataExtractor:
    """Test cases for GraphDataExtractor utility class."""
    
    def test_extract_nodes_by_type(self, simple_graph_data):
        """Test extraction of nodes by type."""
        agent_nodes = GraphDataExtractor.extract_nodes_by_type(simple_graph_data, "agent")
        task_nodes = GraphDataExtractor.extract_nodes_by_type(simple_graph_data, "task")
        
        assert len(agent_nodes) == 1
        assert len(task_nodes) == 1
        assert agent_nodes[0]["id"] == "agent1"
        assert task_nodes[0]["id"] == "task1"
    
    def test_extract_edges_by_type(self, simple_graph_data):
        """Test extraction of edges by type."""
        assignment_edges = GraphDataExtractor.extract_edges_by_type(simple_graph_data, "assignment")
        
        assert len(assignment_edges) == 1
        assert assignment_edges[0]["source"] == "agent1"
        assert assignment_edges[0]["target"] == "task1"
    
    def test_validate_node_structure(self):
        """Test node structure validation."""
        valid_node = {
            "id": "test",
            "type": "agent",
            "data": {
                "role": "Analyst",
                "goal": "Analyze",
                "backstory": "Expert"
            }
        }
        
        errors = GraphDataExtractor.validate_node_structure(valid_node, ["role", "goal", "backstory"])
        assert len(errors) == 0
        
        invalid_node = {
            "id": "test",
            "type": "agent", 
            "data": {
                "role": "Analyst"
                # Missing goal and backstory
            }
        }
        
        errors = GraphDataExtractor.validate_node_structure(invalid_node, ["role", "goal", "backstory"])
        assert len(errors) == 2
        assert any("goal" in error for error in errors)
        assert any("backstory" in error for error in errors)
    
    def test_find_node_relationships(self, complex_graph_data):
        """Test finding node relationships."""
        edges = complex_graph_data["edges"]
        
        # Test research_task relationships
        relationships = GraphDataExtractor.find_node_relationships("research_task", edges)
        assert "researcher" in relationships["incoming"]
        assert "writing_task" in relationships["outgoing"]
        
        # Test writing_task relationships
        relationships = GraphDataExtractor.find_node_relationships("writing_task", edges)
        assert "writer" in relationships["incoming"]
        assert "research_task" in relationships["incoming"]
        assert len(relationships["outgoing"]) == 0 