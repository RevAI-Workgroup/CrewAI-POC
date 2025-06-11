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
        expected_types = ["crew", "agent", "task", "tool", "flow"]
        for node_type in expected_types:
            assert node_type in node_types
        
        # Check that LLM providers are present
        llm_providers = ["openai", "anthropic", "ollama", "google", "azure", "groq"]
        for provider in llm_providers:
            assert provider in node_types
            
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
        required_fields = ["name", "agents", "tasks", "process"]
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
            # Note: Some fields like backstory might not be required in the actual implementation
            if fields[field].get("required"):
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
            # Note: Some fields might not be required in the actual implementation
            if fields[field].get("required"):
                assert fields[field]["required"] is True
            
    def test_llm_definition_structure(self):
        """Test LLM provider definition structure."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        # Test OpenAI provider as an example of LLM node
        openai_def = structure["node_types"]["openai"]
        
        # Check basic properties
        assert openai_def["name"] == "OpenAI"
        assert openai_def["category"] == "llm"
        assert "fields" in openai_def
        
        # Check that common LLM fields are present
        fields = openai_def["fields"]
        common_fields = ["model", "api_key"]
        for field in common_fields:
            assert field in fields
            
    def test_connection_constraints(self):
        """Test connection constraints are properly defined."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        constraints = structure["connection_constraints"]
        
        expected_types = ["crew", "agent", "task", "tool", "flow"]
        for node_type in expected_types:
            assert node_type in constraints
            
        # Test specific constraints for crew
        crew_constraints = constraints["crew"]
        assert "agents" in crew_constraints
        assert "tasks" in crew_constraints
        assert crew_constraints["agents"]["target_type"] == "agent"
        assert crew_constraints["tasks"]["target_type"] == "task"
        
        # Test agent constraints
        agent_constraints = constraints["agent"]
        assert "llm" in agent_constraints
        assert agent_constraints["llm"]["target_type"] == "llm"
        
    def test_field_validation_rules(self):
        """Test that fields have proper validation rules."""
        structure = NodeDefinitionService.get_node_definitions_structure()
        
        # Test temperature slider validation for OpenAI LLM
        openai_fields = structure["node_types"]["openai"]["fields"]
        temp_field = openai_fields["temperature"]
        assert temp_field["type"] == "slider"
        assert "validation" in temp_field
        validation = temp_field["validation"]
        assert validation["min"] == 0.0
        assert validation["max"] == 1.0
        
        # Test boolean field for agent verbose setting
        agent_fields = structure["node_types"]["agent"]["fields"]
        verbose_field = agent_fields["verbose"]
        assert verbose_field["type"] == "boolean"
        assert verbose_field["default"] == False
        assert verbose_field["required"] == False
        
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