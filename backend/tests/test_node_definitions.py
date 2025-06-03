"""
Tests for node definition structure service.
"""

import pytest
from services.node_definitions import NodeDefinitionService


class TestNodeDefinitionService:
    """Test cases for NodeDefinitionService."""
    
    def test_get_node_definitions_structure(self):
        """Test that node definitions structure is generated correctly."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        
        # Check main structure keys
        assert "categories" in structure
        assert "node_types" in structure
        assert "connection_constraints" in structure
        assert "enums" in structure
        
        # Check categories
        categories = structure["categories"]
        assert isinstance(categories, list)
        assert len(categories) > 0
        
        # Check node types
        node_types = structure["node_types"]
        expected_types = ["crew", "agent", "task", "llm", "tool", "flow"]
        for node_type in expected_types:
            assert node_type in node_types
            
    def test_crew_definition_structure(self):
        """Test crew node definition structure."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        crew_def = structure["node_types"]["crew"]
        
        # Check basic properties
        assert crew_def["name"] == "Crew"
        assert crew_def["category"] == "core"
        assert "fields" in crew_def
        
        # Check required fields
        fields = crew_def["fields"]
        required_fields = ["name", "agent_ids", "task_ids", "process"]
        for field in required_fields:
            assert field in fields
            if fields[field].get("required"):
                assert fields[field]["required"] is True
                
    def test_agent_definition_structure(self):
        """Test agent node definition structure."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        agent_def = structure["node_types"]["agent"]
        
        # Check basic properties
        assert agent_def["name"] == "Agent"
        assert agent_def["category"] == "core"
        assert "fields" in agent_def
        
        # Check required fields
        fields = agent_def["fields"]
        required_fields = ["name", "role", "goal", "backstory"]
        for field in required_fields:
            assert field in fields
            assert fields[field]["required"] is True
            
    def test_task_definition_structure(self):
        """Test task node definition structure."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        task_def = structure["node_types"]["task"]
        
        # Check basic properties
        assert task_def["name"] == "Task"
        assert task_def["category"] == "core"
        assert "fields" in task_def
        
        # Check required fields
        fields = task_def["fields"]
        required_fields = ["name", "description", "expected_output"]
        for field in required_fields:
            assert field in fields
            assert fields[field]["required"] is True
            
    def test_llm_definition_structure(self):
        """Test LLM node definition structure."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        llm_def = structure["node_types"]["llm"]
        
        # Check basic properties
        assert llm_def["name"] == "Language Model"
        assert llm_def["category"] == "llm"
        assert "fields" in llm_def
        
        # Check required fields
        fields = llm_def["fields"]
        required_fields = ["name", "provider", "model"]
        for field in required_fields:
            assert field in fields
            assert fields[field]["required"] is True
            
        # Check provider options
        provider_field = fields["provider"]
        assert provider_field["type"] == "select"
        assert "options" in provider_field
        options = provider_field["options"]
        expected_providers = ["openai", "anthropic", "ollama"]
        for provider in expected_providers:
            assert any(opt["value"] == provider for opt in options)
            
    def test_connection_constraints(self):
        """Test connection constraints are properly defined."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        constraints = structure["connection_constraints"]
        
        expected_types = ["crew", "agent", "task", "llm", "tool", "flow"]
        for node_type in expected_types:
            assert node_type in constraints
            constraint = constraints[node_type]
            assert "can_connect_to" in constraint
            assert "can_receive_from" in constraint
            assert "required_connections" in constraint
            
        # Test specific constraints
        crew_constraints = constraints["crew"]
        assert "agent" in crew_constraints["can_connect_to"]
        assert "task" in crew_constraints["can_connect_to"]
        
        agent_constraints = constraints["agent"]
        assert "crew" in agent_constraints["can_receive_from"]
        
    def test_field_validation_rules(self):
        """Test that fields have proper validation rules."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        
        # Test temperature slider validation for LLM
        llm_fields = structure["node_types"]["llm"]["fields"]
        temp_field = llm_fields["temperature"]
        assert temp_field["type"] == "slider"
        assert "validation" in temp_field
        validation = temp_field["validation"]
        assert validation["min"] == 0.0
        assert validation["max"] == 2.0
        
        # Test number field validation for agent max_iter
        agent_fields = structure["node_types"]["agent"]["fields"]
        max_iter_field = agent_fields["max_iter"]
        assert max_iter_field["type"] == "number"
        assert "validation" in max_iter_field
        validation = max_iter_field["validation"]
        assert validation["min"] == 1
        assert validation["max"] == 100
        
    def test_enum_definitions(self):
        """Test enum definitions are properly structured."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        enums = structure["enums"]
        
        expected_enums = ["process_types", "output_formats", "llm_providers"]
        for enum_name in expected_enums:
            assert enum_name in enums
            enum_values = enums[enum_name]
            assert isinstance(enum_values, list)
            
            # Check each enum value has required fields
            for enum_value in enum_values:
                assert "value" in enum_value
                assert "label" in enum_value
                assert "description" in enum_value 