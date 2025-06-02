"""
Validation schemas for CrewAI graph validation.
Provides detailed validation response structures with severity levels and actionable feedback.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    """Individual validation issue with details."""
    severity: ValidationSeverity = Field(..., description="Issue severity level")
    code: str = Field(..., description="Issue code for programmatic handling")
    message: str = Field(..., description="Human-readable issue description")
    node_id: Optional[str] = Field(None, description="Related node ID if applicable")
    edge_id: Optional[str] = Field(None, description="Related edge ID if applicable")
    suggestion: Optional[str] = Field(None, description="Suggested fix")
    location: Optional[Dict[str, Any]] = Field(None, description="Issue location details")


class NodeValidationResult(BaseModel):
    """Validation result for a single node."""
    node_id: str = Field(..., description="Node identifier")
    node_type: str = Field(..., description="Node type")
    is_valid: bool = Field(..., description="Whether node passes validation")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Node issues")
    
    @property
    def has_errors(self) -> bool:
        """Check if node has error-level issues."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        """Check if node has warning-level issues."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)


class EdgeValidationResult(BaseModel):
    """Validation result for a single edge."""
    edge_id: str = Field(..., description="Edge identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    is_valid: bool = Field(..., description="Whether edge passes validation")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Edge issues")


class GraphStructureAnalysis(BaseModel):
    """Analysis of graph structure and topology."""
    total_nodes: int = Field(..., description="Total number of nodes")
    total_edges: int = Field(..., description="Total number of edges")
    entry_points: List[str] = Field(default_factory=list, description="Entry point node IDs")
    exit_points: List[str] = Field(default_factory=list, description="Exit point node IDs")
    isolated_nodes: List[str] = Field(default_factory=list, description="Disconnected node IDs")
    circular_dependencies: List[List[str]] = Field(default_factory=list, description="Circular dependency paths")
    max_depth: int = Field(0, description="Maximum graph depth")
    complexity_score: float = Field(0.0, description="Graph complexity score")


class CrewAICompatibility(BaseModel):
    """CrewAI compatibility assessment."""
    is_compatible: bool = Field(..., description="Whether graph is CrewAI compatible")
    version_requirements: List[str] = Field(default_factory=list, description="Required CrewAI versions")
    feature_usage: Dict[str, bool] = Field(default_factory=dict, description="CrewAI features used")
    compatibility_issues: List[ValidationIssue] = Field(default_factory=list, description="Compatibility issues")


class ValidationMetrics(BaseModel):
    """Validation performance metrics."""
    validation_time_ms: float = Field(..., description="Validation duration in milliseconds")
    nodes_validated: int = Field(..., description="Number of nodes validated")
    edges_validated: int = Field(..., description="Number of edges validated")
    rules_applied: int = Field(..., description="Number of validation rules applied")


class GraphValidationResult(BaseModel):
    """Complete graph validation result."""
    graph_id: str = Field(..., description="Graph identifier")
    is_valid: bool = Field(..., description="Overall validation result")
    
    # Validation results
    node_results: List[NodeValidationResult] = Field(default_factory=list, description="Node validation results")
    edge_results: List[EdgeValidationResult] = Field(default_factory=list, description="Edge validation results")
    global_issues: List[ValidationIssue] = Field(default_factory=list, description="Graph-level issues")
    
    # Analysis results
    structure_analysis: GraphStructureAnalysis = Field(..., description="Graph structure analysis")
    crewai_compatibility: CrewAICompatibility = Field(..., description="CrewAI compatibility check")
    validation_metrics: ValidationMetrics = Field(..., description="Validation performance metrics")
    
    @property
    def total_errors(self) -> int:
        """Count total error-level issues."""
        count = len([i for i in self.global_issues if i.severity == ValidationSeverity.ERROR])
        for node_result in self.node_results:
            count += len([i for i in node_result.issues if i.severity == ValidationSeverity.ERROR])
        for edge_result in self.edge_results:
            count += len([i for i in edge_result.issues if i.severity == ValidationSeverity.ERROR])
        return count
    
    @property
    def total_warnings(self) -> int:
        """Count total warning-level issues."""
        count = len([i for i in self.global_issues if i.severity == ValidationSeverity.WARNING])
        for node_result in self.node_results:
            count += len([i for i in node_result.issues if i.severity == ValidationSeverity.WARNING])
        for edge_result in self.edge_results:
            count += len([i for i in edge_result.issues if i.severity == ValidationSeverity.WARNING])
        return count


class ValidationRuleConfig(BaseModel):
    """Configuration for validation rules."""
    max_nodes: int = Field(100, description="Maximum nodes allowed")
    max_edges: int = Field(200, description="Maximum edges allowed")
    max_depth: int = Field(10, description="Maximum graph depth")
    allow_circular_dependencies: bool = Field(False, description="Allow circular dependencies")
    require_entry_point: bool = Field(True, description="Require at least one entry point")
    require_exit_point: bool = Field(True, description="Require at least one exit point")
    validate_crewai_compatibility: bool = Field(True, description="Validate CrewAI compatibility")
    
    # Performance settings
    enable_caching: bool = Field(True, description="Enable validation caching")
    cache_ttl_seconds: int = Field(300, description="Cache time-to-live in seconds")
    max_validation_time_ms: int = Field(5000, description="Maximum validation time in milliseconds")


# Export schemas
__all__ = [
    "ValidationSeverity",
    "ValidationIssue", 
    "NodeValidationResult",
    "EdgeValidationResult",
    "GraphStructureAnalysis",
    "CrewAICompatibility", 
    "ValidationMetrics",
    "GraphValidationResult",
    "ValidationRuleConfig"
] 