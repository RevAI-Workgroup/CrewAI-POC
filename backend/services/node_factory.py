"""
Node factory for creating and validating CrewAI nodes.
Provides factory patterns and validation logic for all node types.
"""

from typing import Dict, Any, List, Optional, Union, Type
from uuid import uuid4
import re

from schemas.nodes import (
    NodeType, AgentNodeSchema, TaskNodeSchema, ToolNodeSchema, FlowNodeSchema, CrewNodeSchema, LLMNodeSchema,
    BaseNodeSchema, GraphSchema, NodeValidationSchema, GraphValidationSchema
)


class NodeValidationError(Exception):
    """Custom exception for node validation errors."""
    pass


class NodeFactory:
    """Factory class for creating and validating CrewAI nodes."""
    
    @staticmethod
    def create_agent_node(
        name: str,
        role: str,
        goal: str,
        backstory: str,
        **kwargs
    ) -> AgentNodeSchema:
        """Create a new agent node with validation."""
        node_data = {
            "id": kwargs.get("id", f"agent_{uuid4().hex[:8]}"),
            "type": NodeType.AGENT,
            "name": name,
            "role": role,
            "goal": goal,
            "backstory": backstory,
            **kwargs
        }
        
        try:
            return AgentNodeSchema(**node_data)
        except Exception as e:
            raise NodeValidationError(f"Failed to create agent node: {str(e)}")
    
    @staticmethod
    def create_task_node(
        name: str,
        description: str,
        expected_output: str,
        **kwargs
    ) -> TaskNodeSchema:
        """Create a new task node with validation."""
        node_data = {
            "id": kwargs.get("id", f"task_{uuid4().hex[:8]}"),
            "type": NodeType.TASK,
            "name": name,
            "description": description,
            "expected_output": expected_output,
            **kwargs
        }
        
        try:
            return TaskNodeSchema(**node_data)
        except Exception as e:
            raise NodeValidationError(f"Failed to create task node: {str(e)}")
    
    @staticmethod
    def create_tool_node(
        name: str,
        tool_type: str,
        **kwargs
    ) -> ToolNodeSchema:
        """Create a new tool node with validation."""
        node_data = {
            "id": kwargs.get("id", f"tool_{uuid4().hex[:8]}"),
            "type": NodeType.TOOL,
            "name": name,
            "tool_type": tool_type,
            **kwargs
        }
        
        try:
            return ToolNodeSchema(**node_data)
        except Exception as e:
            raise NodeValidationError(f"Failed to create tool node: {str(e)}")
    
    @staticmethod
    def create_flow_node(
        name: str,
        flow_type: str,
        **kwargs
    ) -> FlowNodeSchema:
        """Create a new flow node with validation."""
        node_data = {
            "id": kwargs.get("id", f"flow_{uuid4().hex[:8]}"),
            "type": NodeType.FLOW,
            "name": name,
            "flow_type": flow_type,
            **kwargs
        }
        
        try:
            return FlowNodeSchema(**node_data)
        except Exception as e:
            raise NodeValidationError(f"Failed to create flow node: {str(e)}")
    
    @staticmethod
    def create_crew_node(
        name: str,
        agent_ids: List[str],
        task_ids: List[str],
        **kwargs
    ) -> CrewNodeSchema:
        """Create a new crew node with validation."""
        node_data = {
            "id": kwargs.get("id", f"crew_{uuid4().hex[:8]}"),
            "type": NodeType.CREW,
            "name": name,
            "agent_ids": agent_ids,
            "task_ids": task_ids,
            **kwargs
        }
        
        try:
            return CrewNodeSchema(**node_data)
        except Exception as e:
            raise NodeValidationError(f"Failed to create crew node: {str(e)}")
    
    @staticmethod
    def create_llm_node(
        name: str,
        provider: str,
        model: str,
        **kwargs
    ) -> LLMNodeSchema:
        """Create a new LLM node with validation."""
        node_data = {
            "id": kwargs.get("id", f"llm_{uuid4().hex[:8]}"),
            "type": NodeType.LLM,
            "name": name,
            "provider": provider,
            "model": model,
            **kwargs
        }
        
        try:
            return LLMNodeSchema(**node_data)
        except Exception as e:
            raise NodeValidationError(f"Failed to create LLM node: {str(e)}")


class NodeValidator:
    """Validation logic for nodes and graphs."""
    
    @staticmethod
    def validate_agent_node(node: AgentNodeSchema) -> NodeValidationSchema:
        """Validate an agent node."""
        errors = []
        warnings = []
        
        # Required field validation
        if not node.role.strip():
            errors.append("Agent role cannot be empty")
        elif len(node.role) < 5:
            warnings.append("Agent role is very short, consider providing more detail")
            
        if not node.goal.strip():
            errors.append("Agent goal cannot be empty")
        elif len(node.goal) < 10:
            warnings.append("Agent goal is very short, consider providing more detail")
            
        if not node.backstory.strip():
            errors.append("Agent backstory cannot be empty")
        elif len(node.backstory) < 20:
            warnings.append("Agent backstory is very short, consider providing more context")
        
        # Numeric validation
        if node.max_iter <= 0:
            errors.append("max_iter must be positive")
        elif node.max_iter > 100:
            warnings.append("max_iter is very high, this may cause performance issues")
            
        if node.max_rpm is not None and node.max_rpm <= 0:
            errors.append("max_rpm must be positive if specified")
            
        if node.max_execution_time is not None and node.max_execution_time <= 0:
            errors.append("max_execution_time must be positive if specified")
        
        return NodeValidationSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            node_id=node.id
        )
    
    @staticmethod
    def validate_task_node(node: TaskNodeSchema) -> NodeValidationSchema:
        """Validate a task node."""
        errors = []
        warnings = []
        
        # Required field validation
        if not node.description.strip():
            errors.append("Task description cannot be empty")
        elif len(node.description) < 10:
            warnings.append("Task description is very short, consider providing more detail")
            
        if not node.expected_output.strip():
            errors.append("Task expected_output cannot be empty")
        elif len(node.expected_output) < 10:
            warnings.append("Task expected_output is very short, consider being more specific")
        
        # Output file validation
        if node.output_file:
            if not re.match(r'^[\w\-_./]+\.\w+$', node.output_file):
                errors.append("output_file must be a valid file path with extension")
        
        # Callback validation
        if node.callback:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', node.callback):
                errors.append("callback must be a valid function name")
        
        return NodeValidationSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            node_id=node.id
        )
    
    @staticmethod
    def validate_tool_node(node: ToolNodeSchema) -> NodeValidationSchema:
        """Validate a tool node."""
        errors = []
        warnings = []
        
        # Tool type validation
        if not node.tool_type.strip():
            errors.append("Tool type cannot be empty")
        
        # Custom tool validation
        if node.is_custom and not node.function_name:
            errors.append("Custom tools must have a function_name")
            
        if node.function_name and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', node.function_name):
            errors.append("function_name must be a valid Python function name")
        
        # API endpoint validation
        if node.api_endpoint:
            if not re.match(r'^https?://.+', node.api_endpoint):
                errors.append("api_endpoint must be a valid HTTP/HTTPS URL")
        
        return NodeValidationSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            node_id=node.id
        )
    
    @staticmethod
    def validate_flow_node(node: FlowNodeSchema) -> NodeValidationSchema:
        """Validate a flow node."""
        errors = []
        warnings = []
        
        # Flow type validation is handled by Pydantic enum
        
        # Entry/exit point logic
        if node.entry_point and node.exit_point:
            errors.append("A node cannot be both entry and exit point")
        
        return NodeValidationSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            node_id=node.id
        )
    
    @staticmethod
    def validate_crew_node(node: CrewNodeSchema) -> NodeValidationSchema:
        """Validate a crew node."""
        errors = []
        warnings = []
        
        # Agent and task validation
        if not node.agent_ids or len(node.agent_ids) == 0:
            errors.append("Crew must have at least one agent")
        
        if not node.task_ids or len(node.task_ids) == 0:
            errors.append("Crew must have at least one task")
        
        # Check for duplicate IDs
        if len(node.agent_ids) != len(set(node.agent_ids)):
            errors.append("Duplicate agent IDs found in crew")
            
        if len(node.task_ids) != len(set(node.task_ids)):
            errors.append("Duplicate task IDs found in crew")
        
        # Numeric validation
        if node.max_rpm is not None and node.max_rpm <= 0:
            errors.append("max_rpm must be positive if specified")
            
        if node.max_execution_time is not None and node.max_execution_time <= 0:
            errors.append("max_execution_time must be positive if specified")
        
        # Output file validation
        if node.output_log_file:
            if not re.match(r'^[\w\-_./]+\.\w+$', node.output_log_file):
                errors.append("output_log_file must be a valid file path with extension")
        
        # Callback validation
        if node.step_callback:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', node.step_callback):
                errors.append("step_callback must be a valid function name")
        
        # Warnings for large crews
        if len(node.agent_ids) > 10:
            warnings.append("Large number of agents may impact performance")
            
        if len(node.task_ids) > 20:
            warnings.append("Large number of tasks may impact performance")
        
        return NodeValidationSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            node_id=node.id
        )
    
    @staticmethod
    def validate_llm_node(node: LLMNodeSchema) -> NodeValidationSchema:
        """Validate an LLM node."""
        errors = []
        warnings = []
        
        # Required field validation
        if not node.model.strip():
            errors.append("LLM model name cannot be empty")
        
        # Provider-specific validation
        if node.provider == "openai" and not node.model.startswith(("gpt-", "o1-", "o3-")):
            warnings.append("Model name doesn't match typical OpenAI naming convention")
        elif node.provider == "anthropic" and not node.model.startswith("claude"):
            warnings.append("Model name doesn't match typical Anthropic naming convention")
        elif node.provider == "google" and not node.model.startswith(("gemini", "gemma")):
            warnings.append("Model name doesn't match typical Google naming convention")
        
        # API key validation (basic checks)
        if node.api_key:
            if node.provider == "openai" and not node.api_key.startswith("sk-"):
                errors.append("OpenAI API key should start with 'sk-'")
            elif node.provider == "anthropic" and not node.api_key.startswith("sk-ant-"):
                errors.append("Anthropic API key should start with 'sk-ant-'")
            elif len(node.api_key) < 10:
                errors.append("API key appears to be too short")
        
        # Base URL validation
        if node.base_url and not node.base_url.startswith(('http://', 'https://')):
            errors.append("Base URL must start with http:// or https://")
        
        # Parameter validation
        if node.temperature is not None:
            if node.temperature < 0.0 or node.temperature > 2.0:
                errors.append("Temperature must be between 0.0 and 2.0")
        
        if node.max_tokens is not None and node.max_tokens <= 0:
            errors.append("max_tokens must be positive")
        
        if node.top_p is not None and (node.top_p < 0.0 or node.top_p > 1.0):
            errors.append("top_p must be between 0.0 and 1.0")
        
        if node.frequency_penalty is not None and (node.frequency_penalty < -2.0 or node.frequency_penalty > 2.0):
            errors.append("frequency_penalty must be between -2.0 and 2.0")
        
        if node.presence_penalty is not None and (node.presence_penalty < -2.0 or node.presence_penalty > 2.0):
            errors.append("presence_penalty must be between -2.0 and 2.0")
        
        # Context window validation
        if node.context_window is not None:
            if node.context_window <= 0:
                errors.append("context_window must be positive")
            elif node.context_window > 2000000:  # 2M tokens, very large
                warnings.append("Context window is extremely large, may impact performance")
        
        # Rate limiting validation
        if node.max_rpm is not None and node.max_rpm <= 0:
            errors.append("max_rpm must be positive")
        
        # Timeout validation
        if node.timeout is not None:
            if node.timeout <= 0:
                errors.append("timeout must be positive")
            elif node.timeout > 600:  # 10 minutes
                warnings.append("Timeout is very long, may cause poor user experience")
        
        # Retry validation
        if node.max_retries is not None:
            if node.max_retries < 0:
                errors.append("max_retries cannot be negative")
            elif node.max_retries > 10:
                warnings.append("High retry count may cause excessive delays")
        
        # Provider-specific warnings
        if node.provider == "ollama" and not node.base_url:
            warnings.append("Ollama typically requires a custom base_url (e.g., http://localhost:11434)")
        
        if node.provider == "azure" and not node.azure_deployment:
            warnings.append("Azure provider typically requires azure_deployment parameter")
        
        if node.provider == "google" and not node.vertex_credentials and not node.api_key:
            warnings.append("Google provider requires either vertex_credentials or api_key")
        
        # Cost validation
        if node.cost_per_input_token is not None and node.cost_per_input_token < 0:
            errors.append("cost_per_input_token cannot be negative")
        
        if node.cost_per_output_token is not None and node.cost_per_output_token < 0:
            errors.append("cost_per_output_token cannot be negative")
        
        return NodeValidationSchema(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            node_id=node.id
        )
    
    @classmethod
    def validate_node(cls, node: BaseNodeSchema) -> NodeValidationSchema:
        """Validate any node type."""
        if isinstance(node, AgentNodeSchema):
            return cls.validate_agent_node(node)
        elif isinstance(node, TaskNodeSchema):
            return cls.validate_task_node(node)
        elif isinstance(node, ToolNodeSchema):
            return cls.validate_tool_node(node)
        elif isinstance(node, FlowNodeSchema):
            return cls.validate_flow_node(node)
        elif isinstance(node, CrewNodeSchema):
            return cls.validate_crew_node(node)
        elif isinstance(node, LLMNodeSchema):
            return cls.validate_llm_node(node)
        else:
            return NodeValidationSchema(
                is_valid=False,
                errors=[f"Unknown node type: {type(node)}"],
                warnings=[],
                node_id=getattr(node, 'id', 'unknown')
            )
    
    @classmethod
    def validate_graph(cls, graph: GraphSchema) -> GraphValidationSchema:
        """Validate a complete graph."""
        graph_errors = []
        graph_warnings = []
        node_validations = []
        
        # Validate all nodes
        for node in graph.nodes:
            validation = cls.validate_node(node)
            node_validations.append(validation)
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in graph.nodes]
        if len(node_ids) != len(set(node_ids)):
            graph_errors.append("Duplicate node IDs found in graph")
        
        # Validate edge connections
        for edge in graph.edges:
            source_exists = any(node.id == edge.source_id for node in graph.nodes)
            target_exists = any(node.id == edge.target_id for node in graph.nodes)
            
            if not source_exists:
                graph_errors.append(f"Edge source node {edge.source_id} not found in graph")
            if not target_exists:
                graph_errors.append(f"Edge target node {edge.target_id} not found in graph")
        
        # Check for task dependencies
        task_nodes = [node for node in graph.nodes if node.type == NodeType.TASK]
        for task in task_nodes:
            if hasattr(task, 'context_task_ids'):
                for context_id in task.context_task_ids:
                    if not any(node.id == context_id for node in task_nodes):
                        graph_errors.append(f"Task {task.id} references non-existent context task {context_id}")
        
        # Check for circular dependencies
        if cls._has_circular_dependencies(task_nodes):
            graph_errors.append("Circular task dependencies detected")
        
        # Check for agent-task assignments
        agent_nodes = [node for node in graph.nodes if node.type == NodeType.AGENT]
        for task in task_nodes:
            if hasattr(task, 'agent_id') and task.agent_id:
                if not any(agent.id == task.agent_id for agent in agent_nodes):
                    graph_errors.append(f"Task {task.id} assigned to non-existent agent {task.agent_id}")
        
        # Check LLM references in agents
        llm_nodes = [node for node in graph.nodes if node.type == NodeType.LLM]
        for agent in agent_nodes:
            if hasattr(agent, 'llm') and agent.llm:
                if not any(llm.id == agent.llm for llm in llm_nodes):
                    graph_errors.append(f"Agent {agent.id} references non-existent LLM {agent.llm}")
        
        # Check crew node references
        crew_nodes = [node for node in graph.nodes if node.type == NodeType.CREW]
        for crew in crew_nodes:
            if hasattr(crew, 'agent_ids'):
                for agent_id in crew.agent_ids:
                    if not any(agent.id == agent_id for agent in agent_nodes):
                        graph_errors.append(f"Crew {crew.id} references non-existent agent {agent_id}")
            
            if hasattr(crew, 'task_ids'):
                for task_id in crew.task_ids:
                    if not any(task.id == task_id for task in task_nodes):
                        graph_errors.append(f"Crew {crew.id} references non-existent task {task_id}")
        
        # Graph structure warnings
        if len(agent_nodes) == 0:
            graph_warnings.append("Graph has no agents defined")
        if len(task_nodes) == 0:
            graph_warnings.append("Graph has no tasks defined")
        
        all_valid = all(validation.is_valid for validation in node_validations) and len(graph_errors) == 0
        
        return GraphValidationSchema(
            is_valid=all_valid,
            errors=graph_errors,
            warnings=graph_warnings,
            node_validations=node_validations
        )
    
    @staticmethod
    def _has_circular_dependencies(task_nodes: List[TaskNodeSchema]) -> bool:
        """Check for circular dependencies in task context relationships."""
        # Build dependency graph
        dependencies = {}
        for task in task_nodes:
            dependencies[task.id] = getattr(task, 'context_task_ids', [])
        
        # DFS to detect cycles
        def has_cycle(node_id: str, visited: set, rec_stack: set) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for dep_id in dependencies.get(node_id, []):
                if dep_id not in visited:
                    if has_cycle(dep_id, visited, rec_stack):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        visited = set()
        for task_id in dependencies:
            if task_id not in visited:
                if has_cycle(task_id, visited, set()):
                    return True
        
        return False


# Predefined node templates
class NodeTemplates:
    """Common node templates for quick creation."""
    
    RESEARCH_AGENT = {
        "name": "Research Agent",
        "role": "Senior Research Analyst",
        "goal": "Conduct thorough research and analysis on given topics",
        "backstory": "You are an experienced researcher with expertise in gathering, analyzing, and synthesizing information from multiple sources.",
        "tools": [],
        "memory": True,
        "verbose": False
    }
    
    WRITER_AGENT = {
        "name": "Content Writer",
        "role": "Expert Content Writer",
        "goal": "Create high-quality, engaging content based on research and requirements",
        "backstory": "You are a skilled writer with the ability to transform complex information into clear, compelling content.",
        "tools": [],
        "memory": True,
        "verbose": False
    }
    
    RESEARCH_TASK = {
        "name": "Research Task",
        "description": "Conduct comprehensive research on the specified topic",
        "expected_output": "A detailed research report with key findings and insights",
        "async_execution": False,
        "human_input": False
    }
    
    WRITING_TASK = {
        "name": "Writing Task", 
        "description": "Create content based on the research findings",
        "expected_output": "Well-structured content that meets the specified requirements",
        "async_execution": False,
        "human_input": False
    }
    
    BASIC_CREW = {
        "name": "Basic Crew",
        "agent_ids": [],  # To be filled with actual agent IDs
        "task_ids": [],   # To be filled with actual task IDs
        "process": "sequential",
        "verbose": False,
        "memory": False,
        "cache": True
    }
    
    # LLM Templates
    GPT4_LLM = {
        "name": "GPT-4 Turbo",
        "provider": "openai",
        "model": "gpt-4-turbo-preview",
        "temperature": 0.7,
        "max_tokens": 4000,
        "supports_streaming": True,
        "supports_function_calling": True,
        "context_window": 128000
    }
    
    CLAUDE_LLM = {
        "name": "Claude 3.5 Sonnet",
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 4000,
        "supports_streaming": True,
        "supports_vision": True,
        "context_window": 200000
    }
    
    GEMINI_LLM = {
        "name": "Gemini Pro",
        "provider": "google",
        "model": "gemini-pro",
        "temperature": 0.7,
        "max_tokens": 4000,
        "supports_streaming": True,
        "supports_vision": True,
        "context_window": 1000000
    }
    
    OLLAMA_LLM = {
        "name": "Local Llama",
        "provider": "ollama",
        "model": "llama3.2:latest",
        "base_url": "http://localhost:11434",
        "temperature": 0.7,
        "max_tokens": 4000,
        "supports_streaming": True,
        "context_window": 8192
    }


# Export classes and functions
__all__ = [
    "NodeFactory",
    "NodeValidator", 
    "NodeValidationError",
    "NodeTemplates"
] 