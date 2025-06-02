"""
Graph algorithm utilities for CrewAI graph validation.
Provides efficient algorithms for graph analysis and validation.
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque
import time


class GraphAnalyzer:
    """Efficient graph analysis algorithms for validation."""
    
    def __init__(self, nodes: List[Dict], edges: List[Dict]):
        """Initialize with graph data."""
        self.nodes = {node['id']: node for node in nodes}
        self.edges = edges
        self.adjacency_list = self._build_adjacency_list()
        self.reverse_adjacency_list = self._build_reverse_adjacency_list()
    
    def _build_adjacency_list(self) -> Dict[str, List[str]]:
        """Build adjacency list representation."""
        adj_list = defaultdict(list)
        for edge in self.edges:
            adj_list[edge['source_id']].append(edge['target_id'])
        return dict(adj_list)
    
    def _build_reverse_adjacency_list(self) -> Dict[str, List[str]]:
        """Build reverse adjacency list (incoming edges)."""
        rev_adj_list = defaultdict(list)
        for edge in self.edges:
            rev_adj_list[edge['target_id']].append(edge['source_id'])
        return dict(rev_adj_list)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found cycle - extract the cycle path
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Visit neighbors
            for neighbor in self.adjacency_list.get(node, []):
                if dfs(neighbor, path):
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        # Check all nodes as potential cycle starts
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def find_isolated_nodes(self) -> List[str]:
        """Find nodes with no connections."""
        connected_nodes = set()
        
        # Add all nodes that appear in edges
        for edge in self.edges:
            connected_nodes.add(edge['source_id'])
            connected_nodes.add(edge['target_id'])
        
        # Find nodes not in any edge
        isolated = []
        for node_id in self.nodes:
            if node_id not in connected_nodes:
                isolated.append(node_id)
        
        return isolated
    
    def find_entry_points(self) -> List[str]:
        """Find nodes with no incoming edges."""
        has_incoming = set()
        for edge in self.edges:
            has_incoming.add(edge['target_id'])
        
        entry_points = []
        for node_id in self.nodes:
            if node_id not in has_incoming and node_id in self.adjacency_list:
                entry_points.append(node_id)
        
        return entry_points
    
    def find_exit_points(self) -> List[str]:
        """Find nodes with no outgoing edges."""
        has_outgoing = set()
        for edge in self.edges:
            has_outgoing.add(edge['source_id'])
        
        exit_points = []
        for node_id in self.nodes:
            if node_id not in has_outgoing and node_id in self.reverse_adjacency_list:
                exit_points.append(node_id)
        
        return exit_points
    
    def calculate_max_depth(self) -> int:
        """Calculate maximum graph depth using BFS."""
        entry_points = self.find_entry_points()
        if not entry_points:
            return 0
        
        max_depth = 0
        
        for entry in entry_points:
            visited = set()
            queue = deque([(entry, 0)])
            
            while queue:
                node, depth = queue.popleft()
                
                if node in visited:
                    continue
                
                visited.add(node)
                max_depth = max(max_depth, depth)
                
                # Add neighbors to queue
                for neighbor in self.adjacency_list.get(node, []):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))
        
        return max_depth
    
    def calculate_complexity_score(self) -> float:
        """Calculate graph complexity score."""
        n_nodes = len(self.nodes)
        n_edges = len(self.edges)
        
        if n_nodes == 0:
            return 0.0
        
        # Base complexity: edge density
        max_edges = n_nodes * (n_nodes - 1)  # Directed graph
        edge_density = n_edges / max_edges if max_edges > 0 else 0
        
        # Additional complexity factors
        cycles = len(self.find_circular_dependencies())
        max_depth = self.calculate_max_depth()
        
        # Weighted complexity score (0-100)
        complexity = (
            edge_density * 30 +  # Edge density weight
            (cycles / n_nodes) * 40 +  # Cycle complexity weight  
            (max_depth / n_nodes) * 30  # Depth complexity weight
        )
        
        return min(complexity * 100, 100.0)
    
    def is_reachable(self, start: str, target: str) -> bool:
        """Check if target is reachable from start."""
        if start == target:
            return True
        
        visited = set()
        queue = deque([start])
        
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            
            visited.add(node)
            
            for neighbor in self.adjacency_list.get(node, []):
                if neighbor == target:
                    return True
                if neighbor not in visited:
                    queue.append(neighbor)
        
        return False
    
    def find_strongly_connected_components(self) -> List[List[str]]:
        """Find strongly connected components using Tarjan's algorithm."""
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        index_map = {}
        components = []
        
        def strongconnect(node: str):
            # Set depth index for node
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True
            
            # Consider successors
            for successor in self.adjacency_list.get(node, []):
                if successor not in index:
                    # Successor not yet visited; recurse
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack.get(successor, False):
                    # Successor is in stack and hence in current SCC
                    lowlinks[node] = min(lowlinks[node], index[successor])
            
            # If node is root node, pop stack and create SCC
            if lowlinks[node] == index[node]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == node:
                        break
                components.append(component)
        
        # Run algorithm on all nodes
        for node in self.nodes:
            if node not in index:
                strongconnect(node)
        
        return components
    
    def validate_node_relationships(self) -> List[Tuple[str, str, str]]:
        """Validate node relationship constraints."""
        violations = []
        
        for edge in self.edges:
            source_id = edge['source_id']
            target_id = edge['target_id']
            
            # Check if nodes exist
            if source_id not in self.nodes:
                violations.append((edge['id'], "SOURCE_NOT_FOUND", f"Source node {source_id} not found"))
            
            if target_id not in self.nodes:
                violations.append((edge['id'], "TARGET_NOT_FOUND", f"Target node {target_id} not found"))
            
            if source_id in self.nodes and target_id in self.nodes:
                source_node = self.nodes[source_id]
                target_node = self.nodes[target_id]
                
                # Validate node type relationships
                source_type = source_node.get('type')
                target_type = target_node.get('type')
                
                # Business rule: Agents can connect to Tasks
                if source_type == 'agent' and target_type not in ['task']:
                    violations.append((edge['id'], "INVALID_AGENT_CONNECTION", 
                                     f"Agent nodes can only connect to Task nodes"))
                
                # Business rule: Tasks can connect to other Tasks or Tools
                if source_type == 'task' and target_type not in ['task', 'tool']:
                    violations.append((edge['id'], "INVALID_TASK_CONNECTION",
                                     f"Task nodes can only connect to Task or Tool nodes"))
        
        return violations


# Performance monitoring decorator
def performance_monitor(func):
    """Decorator to monitor function performance."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        return result, execution_time
    return wrapper


# Export utilities
__all__ = [
    "GraphAnalyzer",
    "performance_monitor"
] 