"""
Graph model for storing CrewAI graph definitions
"""

import json
from typing import Dict, List, Any, Optional
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class Graph(BaseModel):
    """
    Model for storing CrewAI graph definitions with nodes, edges, and metadata
    """
    
    # Basic graph information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    
    # Graph data as JSON
    graph_data = Column(JSON, nullable=False)
    
    # Tags for categorization
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Status and control
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)  # For admin templates
    
    # Relationships
    user = relationship("User", back_populates="graphs")
    threads = relationship("Thread", back_populates="graph", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_graph_name'),
    )
    
    def set_graph_data(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set the graph data with nodes and edges"""
        graph_data = {
            "nodes": nodes or [],
            "edges": edges or [],
            "metadata": metadata or {}
        }
        
        # Validate basic structure
        self.validate_graph_structure(graph_data)
        self.graph_data = graph_data
    
    def get_nodes(self) -> List[Dict[str, Any]]:
        """Get the nodes from graph data"""
        graph_data = getattr(self, 'graph_data', None)
        if not graph_data:
            return []
        return graph_data.get("nodes", [])
    
    def get_edges(self) -> List[Dict[str, Any]]:
        """Get the edges from graph data"""
        graph_data = getattr(self, 'graph_data', None)
        if not graph_data:
            return []
        return graph_data.get("edges", [])
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata from graph data"""
        graph_data = getattr(self, 'graph_data', None)
        if not graph_data:
            return {}
        return graph_data.get("metadata", {})
    
    def validate_graph_structure(self, graph_data: Dict[str, Any]) -> bool:
        """Basic validation of graph data structure"""
        if not isinstance(graph_data, dict):
            raise ValueError("Graph data must be a dictionary")
        
        # Check required keys
        if "nodes" not in graph_data:
            raise ValueError("Graph data must contain 'nodes' key")
        
        if "edges" not in graph_data:
            raise ValueError("Graph data must contain 'edges' key")
        
        # Validate nodes
        nodes = graph_data["nodes"]
        if not isinstance(nodes, list):
            raise ValueError("Nodes must be a list")
        
        node_ids = set()
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("Each node must be a dictionary")
            
            if "id" not in node:
                raise ValueError("Each node must have an 'id' field")
            
            node_id = node["id"]
            if node_id in node_ids:
                raise ValueError(f"Duplicate node ID: {node_id}")
            node_ids.add(node_id)
        
        # Validate edges
        edges = graph_data["edges"]
        if not isinstance(edges, list):
            raise ValueError("Edges must be a list")
        
        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError("Each edge must be a dictionary")
            
            if "source" not in edge or "target" not in edge:
                raise ValueError("Each edge must have 'source' and 'target' fields")
            
            # Check that source and target nodes exist
            if edge["source"] not in node_ids:
                raise ValueError(f"Edge source node not found: {edge['source']}")
            
            if edge["target"] not in node_ids:
                raise ValueError(f"Edge target node not found: {edge['target']}")
        
        return True
    
    def increment_version(self) -> None:
        """Increment the graph version"""
        current_version = getattr(self, 'version', None) or 0
        self.version = current_version + 1
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the graph"""
        current_tags = self.get_tags()
        if tag not in current_tags:
            current_tags.append(tag)
            self.set_tags(current_tags)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the graph"""
        current_tags = self.get_tags()
        if tag in current_tags:
            current_tags.remove(tag)
            self.set_tags(current_tags)
    
    def get_tags(self) -> List[str]:
        """Get tags as a list"""
        tags_str = getattr(self, 'tags', None)
        if not tags_str:
            return []
        return [tag.strip() for tag in tags_str.split(",") if tag.strip()]
    
    def set_tags(self, tags: List[str]) -> None:
        """Set tags from a list"""
        if tags:
            self.tags = ",".join([tag.strip() for tag in tags if tag.strip()])
        else:
            self.tags = None
    
    def soft_delete(self) -> None:
        """Soft delete the graph"""
        self.is_active = False
    
    def is_owned_by(self, user_id: str) -> bool:
        """Check if this graph belongs to the given user"""
        return str(self.user_id) == str(user_id)
    
    def can_be_accessed_by(self, user_id: str) -> bool:
        """Check if this graph can be accessed by the given user"""
        # Owner can always access
        if self.is_owned_by(user_id):
            return True
        
        # Templates can be accessed by anyone (read-only for non-admins)
        if getattr(self, 'is_template', False):
            return True
        
        return False
    
    def get_node_count(self) -> int:
        """Get the number of nodes in the graph"""
        return len(self.get_nodes())
    
    def get_edge_count(self) -> int:
        """Get the number of edges in the graph"""
        return len(self.get_edges())
    
    def get_thread_count(self) -> int:
        """Get the number of threads for this graph"""
        return len(getattr(self, 'threads', []))
    
    def __repr__(self) -> str:
        return f"<Graph(id={getattr(self, 'id', None)}, name='{self.name}', user_id='{self.user_id}', version={getattr(self, 'version', 1)})>" 