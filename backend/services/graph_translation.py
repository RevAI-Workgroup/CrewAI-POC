"""
Graph Translation Service

Converts graph data from the database JSON format to CrewAI objects.
Handles translation of nodes (agents, tasks, crews) and edges to executable CrewAI components.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from sqlalchemy.orm import Session

try:
    from ..models.graph import Graph
    from ..schemas.validation import ValidationIssue, ValidationSeverity
except ImportError:
    # Handle case when running as standalone script
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from models.graph import Graph
    from schemas.validation import ValidationIssue, ValidationSeverity

logger = logging.getLogger(__name__)


class GraphTranslationError(Exception):
    """Exception raised when graph translation fails."""
    pass


class GraphTranslationService:
    """Service to translate graph data to CrewAI objects."""
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_issues: List[ValidationIssue] = []
    
    def translate_graph(self, graph: Graph) -> Crew:
        """
        Translate a Graph model instance to a CrewAI Crew object.
        
        Args:
            graph: Graph model instance with graph_data JSON field
            
        Returns:
            CrewAI Crew object ready for execution
            
        Raises:
            GraphTranslationError: If translation fails
        """
        try:
            # Reset validation issues for this translation
            self.validation_issues = []
            
            # Extract graph data
            graph_data = graph.graph_data
            if graph_data is None:
                raise GraphTranslationError("Graph has no graph_data")
            
            # Ensure graph_data is a dict
            if not isinstance(graph_data, dict):
                raise GraphTranslationError("Graph data must be a dictionary")
            
            # Validate basic structure
            self._validate_graph_structure(graph_data)
            
            # Extract nodes and edges
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            metadata = graph_data.get("metadata", {})
            
            # Create lookup dictionaries
            node_lookup = {node["id"]: node for node in nodes}
            
            # Translate nodes to CrewAI objects
            agents = self._translate_agents(nodes, node_lookup)
            tasks = self._translate_tasks(nodes, edges, node_lookup, agents)
            
            # Determine process type
            process_type = self._determine_process_type(nodes, metadata)
            
            # Create and return CrewAI Crew
            crew = Crew(
                agents=list(agents.values()),
                tasks=list(tasks.values()),
                process=process_type,
                verbose=metadata.get("verbose", False),
                memory=metadata.get("memory", False)
            )
            
            logger.info(f"Successfully translated graph {graph.id} to CrewAI Crew")
            return crew
            
        except Exception as e:
            logger.error(f"Failed to translate graph {graph.id}: {str(e)}")
            raise GraphTranslationError(f"Graph translation failed: {str(e)}")
    
    def _validate_graph_structure(self, graph_data: Dict[str, Any]) -> None:
        """Validate basic graph structure before translation."""
        if not isinstance(graph_data, dict):
            raise GraphTranslationError("Graph data must be a dictionary")
        
        if "nodes" not in graph_data:
            raise GraphTranslationError("Graph data must contain 'nodes'")
        
        if "edges" not in graph_data:
            raise GraphTranslationError("Graph data must contain 'edges'")
        
        nodes = graph_data["nodes"]
        if not isinstance(nodes, list):
            raise GraphTranslationError("Nodes must be a list")
        
        # Check for required node types
        agent_nodes = [n for n in nodes if n.get("type") == "agent"]
        task_nodes = [n for n in nodes if n.get("type") == "task"]
        
        if not agent_nodes:
            raise GraphTranslationError("Graph must contain at least one agent node")
        
        if not task_nodes:
            raise GraphTranslationError("Graph must contain at least one task node")
    
    def _translate_agents(self, nodes: List[Dict], node_lookup: Dict[str, Dict]) -> Dict[str, Agent]:
        """
        Translate agent nodes to CrewAI Agent objects.
        
        Args:
            nodes: List of all nodes
            node_lookup: Dictionary for node ID lookup
            
        Returns:
            Dictionary mapping agent IDs to Agent objects
        """
        agents = {}
        
        for node in nodes:
            if node.get("type") != "agent":
                continue
                
            try:
                agent_id = node["id"]
                agent_data = node.get("data", {})
                
                # Extract required fields
                role = agent_data.get("role")
                goal = agent_data.get("goal") 
                backstory = agent_data.get("backstory")
                
                # Validate required fields
                if not role:
                    raise GraphTranslationError(f"Agent {agent_id} missing required field: role")
                if not goal:
                    raise GraphTranslationError(f"Agent {agent_id} missing required field: goal")
                if not backstory:
                    raise GraphTranslationError(f"Agent {agent_id} missing required field: backstory")
                
                # Create CrewAI Agent
                agent = Agent(
                    role=role,
                    goal=goal,
                    backstory=backstory,
                    verbose=agent_data.get("verbose", False),
                    allow_delegation=agent_data.get("allow_delegation", False),
                    max_iter=agent_data.get("max_iter", 20),
                    tools=self._load_agent_tools(agent_data.get("tools", []))
                )
                
                agents[agent_id] = agent
                logger.debug(f"Translated agent: {agent_id} -> {role}")
                
            except Exception as e:
                raise GraphTranslationError(f"Failed to translate agent {node.get('id', 'unknown')}: {str(e)}")
        
        return agents
    
    def _translate_tasks(self, nodes: List[Dict], edges: List[Dict], 
                        node_lookup: Dict[str, Dict], agents: Dict[str, Agent]) -> Dict[str, Task]:
        """
        Translate task nodes to CrewAI Task objects.
        
        Args:
            nodes: List of all nodes
            edges: List of all edges
            node_lookup: Dictionary for node ID lookup
            agents: Dictionary of translated agents
            
        Returns:
            Dictionary mapping task IDs to Task objects
        """
        tasks = {}
        
        # First pass: create tasks without context dependencies
        for node in nodes:
            if node.get("type") != "task":
                continue
                
            try:
                task_id = node["id"]
                task_data = node.get("data", {})
                
                # Extract required fields
                description = task_data.get("description")
                expected_output = task_data.get("expected_output")
                
                # Validate required fields
                if not description:
                    raise GraphTranslationError(f"Task {task_id} missing required field: description")
                if not expected_output:
                    raise GraphTranslationError(f"Task {task_id} missing required field: expected_output")
                
                # Find assigned agent
                assigned_agent = None
                agent_id = task_data.get("agent_id")
                if agent_id and agent_id in agents:
                    assigned_agent = agents[agent_id]
                else:
                    # Try to find agent assignment through edges
                    for edge in edges:
                        if (edge.get("target") == task_id and 
                            edge.get("source") in agents and
                            edge.get("type") == "assignment"):
                            assigned_agent = agents[edge["source"]]
                            break
                
                # Create CrewAI Task (context will be added in second pass)
                task = Task(
                    description=description,
                    expected_output=expected_output,
                    agent=assigned_agent,
                    tools=self._load_task_tools(task_data.get("tools", [])),
                    async_execution=task_data.get("async_execution", False),
                    output_file=task_data.get("output_file"),
                    context=[]  # Will be populated in second pass
                )
                
                tasks[task_id] = task
                logger.debug(f"Translated task: {task_id} -> {description[:50]}...")
                
            except Exception as e:
                raise GraphTranslationError(f"Failed to translate task {node.get('id', 'unknown')}: {str(e)}")
        
        # Second pass: resolve context dependencies
        self._resolve_task_dependencies(tasks, edges)
        
        return tasks
    
    def _resolve_task_dependencies(self, tasks: Dict[str, Task], edges: List[Dict]) -> None:
        """
        Resolve task context dependencies based on edges.
        
        Args:
            tasks: Dictionary of task ID to Task objects
            edges: List of edge definitions
        """
        for edge in edges:
            edge_type = edge.get("type", "default")
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            # Handle context dependencies (task -> task)
            if (edge_type in ["context", "dependency"] and 
                source_id and target_id and
                source_id in tasks and target_id in tasks):
                
                source_task = tasks[source_id]
                target_task = tasks[target_id]
                
                # Add source task as context for target task
                if target_task.context is None:
                    target_task.context = []
                if source_task not in target_task.context:
                    target_task.context.append(source_task)
                    logger.debug(f"Added context dependency: {source_id} -> {target_id}")
    
    def _determine_process_type(self, nodes: List[Dict], metadata: Dict[str, Any]) -> Process:
        """
        Determine the CrewAI process type based on graph structure.
        
        Args:
            nodes: List of all nodes
            metadata: Graph metadata
            
        Returns:
            CrewAI Process type
        """
        # Check for explicit process type in metadata
        process_type = metadata.get("process", "sequential").lower()
        
        # Check for crew nodes that specify process type
        for node in nodes:
            if node.get("type") == "crew":
                crew_process = node.get("data", {}).get("process", "sequential").lower()
                if crew_process == "hierarchical":
                    return Process.hierarchical
        
        # Default behavior based on explicit process type
        if process_type == "hierarchical":
            return Process.hierarchical
        
        return Process.sequential
    
    def _load_agent_tools(self, tool_configs: List[Dict]) -> List[BaseTool]:
        """
        Load tools for an agent based on tool configurations.
        
        Args:
            tool_configs: List of tool configuration dictionaries
            
        Returns:
            List of CrewAI BaseTool instances
        """
        tools = []
        
        for tool_config in tool_configs:
            try:
                tool = self._create_tool_from_config(tool_config)
                if tool:
                    tools.append(tool)
            except Exception as e:
                logger.warning(f"Failed to load tool {tool_config.get('name', 'unknown')}: {str(e)}")
        
        return tools
    
    def _load_task_tools(self, tool_configs: List[Dict]) -> List[BaseTool]:
        """
        Load tools for a task based on tool configurations.
        
        Args:
            tool_configs: List of tool configuration dictionaries
            
        Returns:
            List of CrewAI BaseTool instances
        """
        return self._load_agent_tools(tool_configs)  # Same logic for now
    
    def _create_tool_from_config(self, tool_config: Dict) -> Optional[BaseTool]:
        """
        Create a CrewAI tool from configuration.
        
        Args:
            tool_config: Tool configuration dictionary
            
        Returns:
            CrewAI BaseTool instance or None if creation fails
        """
        tool_type = tool_config.get("type")
        tool_name = tool_config.get("name")
        
        # For now, return None - tool loading will be implemented in future tasks
        logger.debug(f"Tool loading not yet implemented for: {tool_name} ({tool_type})")
        return None
    
    def get_validation_issues(self) -> List[ValidationIssue]:
        """Get validation issues encountered during translation."""
        return self.validation_issues.copy()


class GraphDataExtractor:
    """Utility class for extracting and processing graph data."""
    
    @staticmethod
    def extract_nodes_by_type(graph_data: Dict[str, Any], node_type: str) -> List[Dict]:
        """Extract nodes of a specific type from graph data."""
        nodes = graph_data.get("nodes", [])
        return [node for node in nodes if node.get("type") == node_type]
    
    @staticmethod
    def extract_edges_by_type(graph_data: Dict[str, Any], edge_type: str) -> List[Dict]:
        """Extract edges of a specific type from graph data."""
        edges = graph_data.get("edges", [])
        return [edge for edge in edges if edge.get("type") == edge_type]
    
    @staticmethod
    def validate_node_structure(node: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that a node has required fields."""
        errors = []
        node_data = node.get("data", {})
        
        for field in required_fields:
            if field not in node_data or not node_data[field]:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    @staticmethod
    def find_node_relationships(node_id: str, edges: List[Dict]) -> Dict[str, List[str]]:
        """Find all relationships for a given node."""
        relationships = {
            "incoming": [],
            "outgoing": []
        }
        
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            
            if source == node_id:
                relationships["outgoing"].append(target)
            elif target == node_id:
                relationships["incoming"].append(source)
        
        return relationships 