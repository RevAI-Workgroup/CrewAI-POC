"""
Core graph validation service for CrewAI graphs.
Provides comprehensive validation including structural, semantic, and business rule validation.
"""

from typing import Dict, List, Optional, Any
import time
import hashlib
import json
from datetime import datetime, timedelta

from backend.schemas.nodes import GraphSchema, NodeType
from backend.schemas.validation import (
    ValidationSeverity, ValidationIssue, NodeValidationResult,
    EdgeValidationResult, GraphStructureAnalysis, CrewAICompatibility,
    ValidationMetrics, GraphValidationResult, ValidationRuleConfig
)
from backend.utils.graph_algorithms import GraphAnalyzer, performance_monitor


class ValidationCache:
    """Simple in-memory cache for validation results."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict] = {}
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, graph_data: Dict) -> str:
        """Generate cache key from graph data."""
        graph_str = json.dumps(graph_data, sort_keys=True)
        return hashlib.md5(graph_str.encode()).hexdigest()
    
    def get(self, graph_data: Dict) -> Optional[GraphValidationResult]:
        """Get cached validation result."""
        key = self._generate_key(graph_data)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expires']:
                return entry['result']
            else:
                del self.cache[key]
        return None
    
    def set(self, graph_data: Dict, result: GraphValidationResult) -> None:
        """Cache validation result."""
        key = self._generate_key(graph_data)
        expires = datetime.now() + timedelta(seconds=self.ttl_seconds)
        self.cache[key] = {
            'result': result,
            'expires': expires
        }
    
    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()


class CrewAIValidator:
    """Validates CrewAI compatibility and semantic correctness."""
    
    def __init__(self):
        self.supported_versions = ["0.121.1", "0.121.0", "0.120.0"]
        self.required_features = {
            "agents": ["role", "goal", "backstory"],
            "tasks": ["description", "expected_output"],
            "tools": ["tool_type"],
            "flows": ["flow_type"],
            "crews": ["agent_ids", "task_ids", "process"]
        }
    
    def validate_compatibility(self, graph_data: Dict) -> CrewAICompatibility:
        """Validate CrewAI compatibility."""
        issues = []
        feature_usage = {}
        
        nodes = graph_data.get('nodes', [])
        
        # Check for required components
        agent_nodes = [n for n in nodes if n.get('type') == 'agent']
        task_nodes = [n for n in nodes if n.get('type') == 'task']
        crew_nodes = [n for n in nodes if n.get('type') == 'crew']
        
        if not agent_nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="NO_AGENTS",
                message="CrewAI requires at least one agent",
                node_id=None,
                edge_id=None,
                suggestion="Add an agent node to the graph",
                location=None
            ))
        
        if not task_nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="NO_TASKS", 
                message="CrewAI requires at least one task",
                node_id=None,
                edge_id=None,
                suggestion="Add a task node to the graph",
                location=None
            ))
        
        # Validate agent properties
        for agent in agent_nodes:
            self._validate_agent_properties(agent, issues)
        
        # Validate task properties
        for task in task_nodes:
            self._validate_task_properties(task, issues)
            
        # Validate crew properties
        for crew in crew_nodes:
            self._validate_crew_properties(crew, issues, nodes)
        
        # Check feature usage
        feature_usage['agents'] = len(agent_nodes) > 0
        feature_usage['tasks'] = len(task_nodes) > 0
        feature_usage['tools'] = any(n.get('type') == 'tool' for n in nodes)
        feature_usage['flows'] = any(n.get('type') == 'flow' for n in nodes)
        feature_usage['crews'] = len(crew_nodes) > 0
        feature_usage['hierarchical'] = any(
            n.get('flow_type') == 'hierarchical' or n.get('process') == 'hierarchical' 
            for n in nodes if n.get('type') in ['flow', 'crew']
        )
        
        is_compatible = len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0
        
        return CrewAICompatibility(
            is_compatible=is_compatible,
            version_requirements=self.supported_versions,
            feature_usage=feature_usage,
            compatibility_issues=issues
        )
    
    def _validate_agent_properties(self, agent: Dict, issues: List[ValidationIssue]) -> None:
        """Validate individual agent properties."""
        required_fields = ["role", "goal", "backstory"]
        
        for field in required_fields:
            value = agent.get(field)
            if not value or not str(value).strip():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code=f"AGENT_MISSING_{field.upper()}",
                    message=f"Agent {agent.get('id')} missing required field: {field}",
                    node_id=agent.get('id'),
                    edge_id=None,
                    suggestion=f"Add a {field} value to the agent",
                    location=None
                ))
        
        # Validate optional constraints
        max_iter = agent.get('max_iter', 20)
        if max_iter <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="AGENT_INVALID_MAX_ITER",
                message=f"Agent {agent.get('id')} has invalid max_iter: {max_iter}",
                node_id=agent.get('id'),
                edge_id=None,
                suggestion="Set max_iter to a positive integer",
                location=None
            ))
    
    def _validate_task_properties(self, task: Dict, issues: List[ValidationIssue]) -> None:
        """Validate individual task properties."""
        required_fields = ["description", "expected_output"]
        
        for field in required_fields:
            value = task.get(field)
            if not value or not str(value).strip():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code=f"TASK_MISSING_{field.upper()}",
                    message=f"Task {task.get('id')} missing required field: {field}",
                    node_id=task.get('id'),
                    edge_id=None,
                    suggestion=f"Add a {field} value to the task",
                    location=None
                ))
    
    def _validate_crew_properties(self, crew: Dict, issues: List[ValidationIssue], all_nodes: List[Dict]) -> None:
        """Validate individual crew properties."""
        crew_id = crew.get('id')
        
        # Validate required fields
        agent_ids = crew.get('agent_ids', [])
        task_ids = crew.get('task_ids', [])
        process = crew.get('process')
        
        if not agent_ids:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="CREW_MISSING_AGENTS",
                message=f"Crew {crew_id} must have at least one agent",
                node_id=crew_id,
                edge_id=None,
                suggestion="Add agent IDs to the crew configuration",
                location=None
            ))
        
        if not task_ids:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="CREW_MISSING_TASKS",
                message=f"Crew {crew_id} must have at least one task",
                node_id=crew_id,
                edge_id=None,
                suggestion="Add task IDs to the crew configuration",
                location=None
            ))
        
        if not process:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="CREW_MISSING_PROCESS",
                message=f"Crew {crew_id} must specify a process type",
                node_id=crew_id,
                edge_id=None,
                suggestion="Set process to 'sequential' or 'hierarchical'",
                location=None
            ))
        
        # Create lookup for nodes by ID and type
        node_lookup = {node['id']: node for node in all_nodes}
        agent_nodes = {node['id']: node for node in all_nodes if node.get('type') == 'agent'}
        task_nodes = {node['id']: node for node in all_nodes if node.get('type') == 'task'}
        
        # Validate agent references
        for agent_id in agent_ids:
            if agent_id not in node_lookup:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="CREW_INVALID_AGENT_REF",
                    message=f"Crew {crew_id} references non-existent agent: {agent_id}",
                    node_id=crew_id,
                    edge_id=None,
                    suggestion=f"Ensure agent {agent_id} exists in the graph or remove from crew",
                    location=None
                ))
            elif agent_id not in agent_nodes:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="CREW_INVALID_AGENT_TYPE",
                    message=f"Crew {crew_id} references node {agent_id} which is not an agent",
                    node_id=crew_id,
                    edge_id=None,
                    suggestion=f"Ensure {agent_id} is an agent node or remove from crew agents",
                    location=None
                ))
        
        # Validate task references
        for task_id in task_ids:
            if task_id not in node_lookup:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="CREW_INVALID_TASK_REF",
                    message=f"Crew {crew_id} references non-existent task: {task_id}",
                    node_id=crew_id,
                    edge_id=None,
                    suggestion=f"Ensure task {task_id} exists in the graph or remove from crew",
                    location=None
                ))
            elif task_id not in task_nodes:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="CREW_INVALID_TASK_TYPE",
                    message=f"Crew {crew_id} references node {task_id} which is not a task",
                    node_id=crew_id,
                    edge_id=None,
                    suggestion=f"Ensure {task_id} is a task node or remove from crew tasks",
                    location=None
                ))
        
        # Validate process type
        valid_processes = ['sequential', 'hierarchical']
        if process and process not in valid_processes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="CREW_INVALID_PROCESS",
                message=f"Crew {crew_id} has invalid process type: {process}",
                node_id=crew_id,
                edge_id=None,
                suggestion=f"Use one of: {valid_processes}",
                location=None
            ))
        
        # Validate hierarchical process requirements
        if process == 'hierarchical' and len(agent_ids) > 0:
            # In hierarchical process, there should be a manager agent
            # This is a warning since it's not strictly required but recommended
            manager_found = False
            for agent_id in agent_ids:
                agent = agent_nodes.get(agent_id, {})
                if agent.get('allow_delegation'):
                    manager_found = True
                    break
            
            if not manager_found:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="CREW_HIERARCHICAL_NO_MANAGER",
                    message=f"Crew {crew_id} uses hierarchical process but no agent has delegation enabled",
                    node_id=crew_id,
                    edge_id=None,
                    suggestion="Enable 'allow_delegation' for at least one agent to act as manager",
                    location=None
                ))


class GraphValidationService:
    """Main graph validation service."""
    
    def __init__(self, config: Optional[ValidationRuleConfig] = None):
        if config is None:
            self.config = ValidationRuleConfig(
                max_nodes=100,
                max_edges=200,
                max_depth=10,
                allow_circular_dependencies=False,
                require_entry_point=True,
                require_exit_point=True,
                validate_crewai_compatibility=True,
                enable_caching=True,
                cache_ttl_seconds=300,
                max_validation_time_ms=5000
            )
        else:
            self.config = config
        self.cache = ValidationCache(self.config.cache_ttl_seconds) if self.config.enable_caching else None
        self.crewai_validator = CrewAIValidator()
    
    @performance_monitor
    def validate_graph(self, graph: GraphSchema) -> GraphValidationResult:
        """Perform comprehensive graph validation."""
        # Convert to dict for processing
        graph_data = graph.dict()
        
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(graph_data)
            if cached_result:
                return cached_result
        
        start_time = time.time()
        
        # Initialize result
        result = GraphValidationResult(
            graph_id=graph.id,
            is_valid=True,
            node_results=[],
            edge_results=[],
            global_issues=[],
            structure_analysis=GraphStructureAnalysis(
                total_nodes=0,
                total_edges=0,
                max_depth=0,
                complexity_score=0.0
            ),
            crewai_compatibility=CrewAICompatibility(is_compatible=True),
            validation_metrics=ValidationMetrics(
                validation_time_ms=0,
                nodes_validated=0,
                edges_validated=0,
                rules_applied=0
            )
        )
        
        try:
            # Validate graph size limits
            self._validate_graph_limits(graph_data, result)
            
            # Perform structural analysis
            self._analyze_graph_structure(graph_data, result)
            
            # Validate individual nodes
            self._validate_nodes(graph_data, result)
            
            # Validate edges
            self._validate_edges(graph_data, result)
            
            # Validate CrewAI compatibility
            result.crewai_compatibility = self.crewai_validator.validate_compatibility(graph_data)
            
            # Determine overall validity
            result.is_valid = (
                result.total_errors == 0 and 
                result.crewai_compatibility.is_compatible
            )
            
        except Exception as e:
            # Handle validation errors gracefully
            result.global_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="VALIDATION_EXCEPTION",
                message=f"Validation failed with exception: {str(e)}",
                node_id=None,
                edge_id=None,
                suggestion="Check graph data format and try again",
                location=None
            ))
            result.is_valid = False
        
        # Finalize metrics
        end_time = time.time()
        result.validation_metrics.validation_time_ms = (end_time - start_time) * 1000
        result.validation_metrics.nodes_validated = len(graph_data.get('nodes', []))
        result.validation_metrics.edges_validated = len(graph_data.get('edges', []))
        result.validation_metrics.rules_applied = self._count_rules_applied()
        
        # Cache result
        if self.cache:
            self.cache.set(graph_data, result)
        
        return result
    
    def _validate_graph_limits(self, graph_data: Dict, result: GraphValidationResult) -> None:
        """Validate graph size and complexity limits."""
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        # Check node count limit
        if len(nodes) > self.config.max_nodes:
            result.global_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="TOO_MANY_NODES",
                message=f"Graph has {len(nodes)} nodes, maximum allowed is {self.config.max_nodes}",
                node_id=None,
                edge_id=None,
                suggestion=f"Reduce graph to {self.config.max_nodes} nodes or fewer",
                location=None
            ))
        
        # Check edge count limit
        if len(edges) > self.config.max_edges:
            result.global_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="TOO_MANY_EDGES",
                message=f"Graph has {len(edges)} edges, maximum allowed is {self.config.max_edges}",
                node_id=None,
                edge_id=None,
                suggestion=f"Reduce graph to {self.config.max_edges} edges or fewer",
                location=None
            ))
    
    def _analyze_graph_structure(self, graph_data: Dict, result: GraphValidationResult) -> None:
        """Analyze graph structure and topology."""
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        if not nodes:
            result.structure_analysis = GraphStructureAnalysis(
                total_nodes=0,
                total_edges=0,
                max_depth=0,
                complexity_score=0.0
            )
            return
        
        analyzer = GraphAnalyzer(nodes, edges)
        
        # Analyze structure
        entry_points = analyzer.find_entry_points()
        exit_points = analyzer.find_exit_points()
        isolated_nodes = analyzer.find_isolated_nodes()
        circular_deps = analyzer.find_circular_dependencies()
        max_depth = analyzer.calculate_max_depth()
        complexity = analyzer.calculate_complexity_score()
        
        result.structure_analysis = GraphStructureAnalysis(
            total_nodes=len(nodes),
            total_edges=len(edges),
            entry_points=entry_points,
            exit_points=exit_points,
            isolated_nodes=isolated_nodes,
            circular_dependencies=circular_deps,
            max_depth=max_depth,
            complexity_score=complexity
        )
        
        # Add structural validation issues
        if self.config.require_entry_point and not entry_points:
            result.global_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="NO_ENTRY_POINT",
                message="Graph has no entry points (nodes with no incoming edges)",
                node_id=None,
                edge_id=None,
                suggestion="Add at least one node with no incoming connections",
                location=None
            ))
        
        if self.config.require_exit_point and not exit_points:
            result.global_issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="NO_EXIT_POINT", 
                message="Graph has no exit points (nodes with no outgoing edges)",
                node_id=None,
                edge_id=None,
                suggestion="Add at least one node with no outgoing connections",
                location=None
            ))
        
        if not self.config.allow_circular_dependencies and circular_deps:
            for cycle in circular_deps:
                result.global_issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="CIRCULAR_DEPENDENCY",
                    message=f"Circular dependency detected: {' -> '.join(cycle)}",
                    node_id=None,
                    edge_id=None,
                    suggestion="Remove circular references by breaking the cycle",
                    location=None
                ))
        
        if isolated_nodes:
            for node_id in isolated_nodes:
                result.global_issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="ISOLATED_NODE",
                    message=f"Node {node_id} is isolated (no connections)",
                    node_id=node_id,
                    edge_id=None,
                    suggestion="Connect the node to the graph or remove it",
                    location=None
                ))
        
        if max_depth > self.config.max_depth:
            result.global_issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="EXCESSIVE_DEPTH",
                message=f"Graph depth ({max_depth}) exceeds recommended maximum ({self.config.max_depth})",
                node_id=None,
                edge_id=None,
                suggestion="Consider flattening the graph structure",
                location=None
            ))
    
    def _validate_nodes(self, graph_data: Dict, result: GraphValidationResult) -> None:
        """Validate individual nodes."""
        nodes = graph_data.get('nodes', [])
        
        for node in nodes:
            node_result = self._validate_single_node(node)
            result.node_results.append(node_result)
    
    def _validate_single_node(self, node: Dict) -> NodeValidationResult:
        """Validate a single node."""
        issues = []
        node_id = node.get('id', 'unknown')
        node_type = node.get('type', 'unknown')
        
        # Basic node validation
        if not node_id:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MISSING_NODE_ID",
                message="Node is missing required ID field",
                node_id=None,
                edge_id=None,
                suggestion="Add a unique ID to the node",
                location=None
            ))
        
        if not node_type or node_type not in [nt.value for nt in NodeType]:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="INVALID_NODE_TYPE",
                message=f"Node {node_id} has invalid type: {node_type}",
                node_id=node_id,
                edge_id=None,
                suggestion=f"Use one of: {[nt.value for nt in NodeType]}",
                location=None
            ))
        
        # Type-specific validation
        if node_type == NodeType.AGENT.value:
            self._validate_agent_node(node, issues)
        elif node_type == NodeType.TASK.value:
            self._validate_task_node(node, issues)
        elif node_type == NodeType.TOOL.value:
            self._validate_tool_node(node, issues)
        elif node_type == NodeType.FLOW.value:
            self._validate_flow_node(node, issues)
        elif node_type == NodeType.CREW.value:
            self._validate_crew_node(node, issues)
        
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return NodeValidationResult(
            node_id=node_id,
            node_type=node_type,
            is_valid=is_valid,
            issues=issues
        )
    
    def _validate_agent_node(self, node: Dict, issues: List[ValidationIssue]) -> None:
        """Validate agent-specific properties."""
        required_fields = ["role", "goal", "backstory"]
        
        for field in required_fields:
            if not node.get(field):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code=f"AGENT_MISSING_{field.upper()}",
                    message=f"Agent node missing required field: {field}",
                    node_id=node.get('id'),
                    edge_id=None,
                    suggestion=f"Add {field} to the agent configuration",
                    location=None
                ))
    
    def _validate_task_node(self, node: Dict, issues: List[ValidationIssue]) -> None:
        """Validate task-specific properties."""
        required_fields = ["description", "expected_output"]
        
        for field in required_fields:
            if not node.get(field):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code=f"TASK_MISSING_{field.upper()}",
                    message=f"Task node missing required field: {field}",
                    node_id=node.get('id'),
                    edge_id=None,
                    suggestion=f"Add {field} to the task configuration",
                    location=None
                ))
    
    def _validate_tool_node(self, node: Dict, issues: List[ValidationIssue]) -> None:
        """Validate tool-specific properties."""
        if not node.get('tool_type'):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="TOOL_MISSING_TYPE",
                message="Tool node missing required tool_type field",
                node_id=node.get('id'),
                edge_id=None,
                suggestion="Specify the tool type",
                location=None
            ))
    
    def _validate_flow_node(self, node: Dict, issues: List[ValidationIssue]) -> None:
        """Validate flow-specific properties."""
        if not node.get('flow_type'):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="FLOW_MISSING_TYPE",
                message="Flow node missing required flow_type field",
                node_id=node.get('id'),
                edge_id=None,
                suggestion="Specify the flow type (sequential, hierarchical, etc.)",
                location=None
            ))
    
    def _validate_crew_node(self, node: Dict, issues: List[ValidationIssue]) -> None:
        """Validate crew-specific properties."""
        required_fields = ["agent_ids", "task_ids", "process"]
        
        for field in required_fields:
            value = node.get(field)
            if field in ["agent_ids", "task_ids"]:
                # These should be non-empty lists
                if not value or not isinstance(value, list) or len(value) == 0:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code=f"CREW_MISSING_{field.upper()}",
                        message=f"Crew node missing required field: {field}",
                        node_id=node.get('id'),
                        edge_id=None,
                        suggestion=f"Add at least one {field.replace('_ids', '')} to the crew",
                        location=None
                    ))
            else:
                # Regular required field
                if not value:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code=f"CREW_MISSING_{field.upper()}",
                        message=f"Crew node missing required field: {field}",
                        node_id=node.get('id'),
                        edge_id=None,
                        suggestion=f"Add {field} to the crew configuration",
                        location=None
                    ))
        
        # Validate process type
        process = node.get('process')
        if process and process not in ['sequential', 'hierarchical']:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="CREW_INVALID_PROCESS",
                message=f"Crew node has invalid process type: {process}",
                node_id=node.get('id'),
                edge_id=None,
                suggestion="Use 'sequential' or 'hierarchical' for process type",
                location=None
            ))
    
    def _validate_edges(self, graph_data: Dict, result: GraphValidationResult) -> None:
        """Validate graph edges."""
        edges = graph_data.get('edges', [])
        nodes = {node['id']: node for node in graph_data.get('nodes', [])}
        
        for edge in edges:
            edge_result = self._validate_single_edge(edge, nodes)
            result.edge_results.append(edge_result)
    
    def _validate_single_edge(self, edge: Dict, nodes: Dict) -> EdgeValidationResult:
        """Validate a single edge."""
        issues = []
        edge_id = edge.get('id', 'unknown')
        source_id = edge.get('source_id')
        target_id = edge.get('target_id')
        
        # Check edge structure
        if not source_id:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="EDGE_MISSING_SOURCE",
                message=f"Edge {edge_id} missing source_id",
                node_id=None,
                edge_id=edge_id,
                suggestion="Add source node ID to the edge",
                location=None
            ))
        
        if not target_id:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="EDGE_MISSING_TARGET",
                message=f"Edge {edge_id} missing target_id",
                node_id=None,
                edge_id=edge_id,
                suggestion="Add target node ID to the edge",
                location=None
            ))
        
        # Check node existence
        if source_id and source_id not in nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="EDGE_SOURCE_NOT_FOUND",
                message=f"Edge {edge_id} references non-existent source node: {source_id}",
                node_id=None,
                edge_id=edge_id,
                suggestion="Ensure source node exists in the graph",
                location=None
            ))
        
        if target_id and target_id not in nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="EDGE_TARGET_NOT_FOUND",
                message=f"Edge {edge_id} references non-existent target node: {target_id}",
                node_id=None,
                edge_id=edge_id,
                suggestion="Ensure target node exists in the graph",
                location=None
            ))
        
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return EdgeValidationResult(
            edge_id=edge_id,
            source_id=source_id or "",
            target_id=target_id or "",
            is_valid=is_valid,
            issues=issues
        )
    
    def _count_rules_applied(self) -> int:
        """Count the number of validation rules applied."""
        # Updated count to include crew validation rules
        return 20  # Basic count of validation rules including crew validation
    
    def clear_cache(self) -> None:
        """Clear validation cache."""
        if self.cache:
            self.cache.clear()


# Export the service
__all__ = [
    "GraphValidationService",
    "ValidationCache",
    "CrewAIValidator"
] 