"""
Graph crew validation service for chat functionality.

Validates that graphs meet the requirements for chat interface:
- Exactly one crew node per graph
- Crew node has valid configuration
- Crew is properly connected to agents and tasks
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from models.graph import Graph
from models.node_types import NodeTypeEnum

logger = logging.getLogger(__name__)


class GraphCrewValidationService:
    """Service for validating crew configuration in graphs for chat functionality."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_graph_for_chat(self, graph: Graph) -> Dict[str, Any]:
        """
        Validate a graph for chat functionality.
        
        Returns validation result with details about the crew configuration.
        """
        validation_result = {
            'is_valid': False,
            'crew_node_id': None,
            'crew_config': None,
            'agent_count': 0,
            'task_count': 0,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Basic graph data validation
            graph_data = getattr(graph, 'graph_data', None)
            if not graph_data:
                validation_result['errors'].append("Graph has no data")
                return validation_result
            
            nodes = graph_data.get('nodes', [])
            if not nodes:
                validation_result['errors'].append("Graph has no nodes")
                return validation_result
            
            # Find crew nodes
            crew_nodes = [node for node in nodes if node.get('type') == NodeTypeEnum.CREW.value]
            
            if len(crew_nodes) == 0:
                validation_result['errors'].append("Graph must have at least one crew node for chat interface")
                return validation_result
            
            if len(crew_nodes) > 1:
                validation_result['errors'].append(
                    f"Graph can only have one crew node for chat interface, but found {len(crew_nodes)} crew nodes"
                )
                return validation_result
            
            # Validate the single crew node
            crew_node = crew_nodes[0]
            validation_result['crew_node_id'] = crew_node.get('id')
            
            if not crew_node.get('id'):
                validation_result['errors'].append("Crew node must have an id")
                return validation_result
            
            # Extract crew configuration
            crew_config = crew_node.get('data', {}) or crew_node.get('config', {})
            validation_result['crew_config'] = crew_config
            
            # Validate crew has agents and tasks
            agent_ids = crew_config.get('agent_ids', [])
            task_ids = crew_config.get('task_ids', [])
            
            validation_result['agent_count'] = len(agent_ids)
            validation_result['task_count'] = len(task_ids)
            
            if not agent_ids:
                validation_result['warnings'].append("Crew has no agents assigned")
            
            if not task_ids:
                validation_result['warnings'].append("Crew has no tasks assigned")
            
            # Validate agent and task nodes exist in graph
            node_ids = {node.get('id') for node in nodes}
            
            missing_agents = [aid for aid in agent_ids if aid not in node_ids]
            if missing_agents:
                validation_result['errors'].append(
                    f"Crew references non-existent agent nodes: {missing_agents}"
                )
                return validation_result
            
            missing_tasks = [tid for tid in task_ids if tid not in node_ids]
            if missing_tasks:
                validation_result['errors'].append(
                    f"Crew references non-existent task nodes: {missing_tasks}"
                )
                return validation_result
            
            # All validations passed
            validation_result['is_valid'] = True
            
            logger.debug(
                f"Graph {graph.id} validated for chat: crew_id={validation_result['crew_node_id']}, "
                f"agents={validation_result['agent_count']}, tasks={validation_result['task_count']}"
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate graph {graph.id} for chat: {e}")
            validation_result['errors'].append(f"Validation failed: {str(e)}")
            return validation_result
    
    def validate_single_crew_restriction(self, graph: Graph) -> None:
        """
        Validate single crew restriction and raise exception if invalid.
        
        This method provides a simple interface for thread creation validation.
        """
        validation_result = self.validate_graph_for_chat(graph)
        
        if not validation_result['is_valid']:
            errors = validation_result['errors']
            raise ValueError(f"Graph validation failed: {'; '.join(errors)}")
        
        # Log warnings if any
        if validation_result['warnings']:
            warnings = validation_result['warnings']
            logger.warning(f"Graph {graph.id} validation warnings: {'; '.join(warnings)}")
    
    def get_crew_node_from_graph(self, graph: Graph) -> Optional[Dict[str, Any]]:
        """
        Get the crew node from a validated graph.
        
        Returns None if graph is not valid for chat.
        """
        validation_result = self.validate_graph_for_chat(graph)
        
        if not validation_result['is_valid']:
            return None
        
        # Find and return the crew node
        graph_data = getattr(graph, 'graph_data', {})
        nodes = graph_data.get('nodes', [])
        
        for node in nodes:
            if node.get('id') == validation_result['crew_node_id']:
                return node
        
        return None
    
    def check_graph_has_active_threads(self, graph_id: str) -> bool:
        """
        Check if graph already has active threads (additional restriction).
        
        This enforces the one-thread-per-graph policy.
        """
        from models.thread import Thread, ThreadStatus
        
        active_threads = self.db.query(Thread).filter(
            Thread.graph_id == graph_id,
            Thread.status == ThreadStatus.ACTIVE.value  # type: ignore
        ).count()
        
        return active_threads > 0
    
    def validate_graph_for_new_thread(self, graph: Graph) -> None:
        """
        Complete validation for creating a new thread.
        
        Validates both single crew restriction and no existing active threads.
        """
        # First validate single crew restriction
        self.validate_single_crew_restriction(graph)
        
        # Then check for existing active threads
        if self.check_graph_has_active_threads(str(graph.id)):
            raise ValueError(
                "Graph already has an active chat thread. Only one active thread per graph is allowed."
            )
        
        logger.info(f"Graph {str(graph.id)} validated for new thread creation") 