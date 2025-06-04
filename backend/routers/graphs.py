"""
Graph management router for CrewAI backend API.
Provides CRUD operations for graphs and node definition structure metadata.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.graph import Graph
from models.user import User
from schemas.nodes import GraphSchema
from services.node_definitions import NodeDefinitionService
from utils.dependencies import get_db, get_current_user

router = APIRouter(tags=["graphs"])


@router.get("/graphs/nodes")
async def get_node_definitions(
    current_user: User = Depends(get_current_user)
):
    """
    Get node definition structure for frontend rendering.

    Returns metadata for all node types including field requirements,
    types, validation rules, and connection constraints.
    """
    try:
        structure = NodeDefinitionService.get_node_definitions_structure()
        return {
            "success": True,
            "data": structure
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate node definitions structure: {str(e)}"
        )


@router.get("/graphs")
async def list_graphs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all graphs for the current user.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user

    Returns:
        List of user's graphs
    """
    try:
        graphs = db.query(Graph).filter(
            Graph.user_id == current_user.id
        ).offset(skip).limit(limit).all()

        return {
            "success": True,
            "data": graphs,
            "count": len(graphs)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve graphs: {str(e)}"
        )


@router.get("/graphs/{graph_id}")
async def get_graph(
    graph_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific graph by ID.

    Args:
        graph_id: Graph identifier
        db: Database session
        current_user: Authenticated user

    Returns:
        Graph data with nodes and connections
    """
    try:
        graph = db.query(Graph).filter(
            Graph.id == graph_id,
            Graph.user_id == current_user.id
        ).first()

        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found"
            )

        return {
            "success": True,
            "data": graph
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve graph: {str(e)}"
        )


@router.post("/graphs")
async def create_graph(
    graph_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new graph.

    Args:
        graph_data: Graph creation data (name, description, etc.)
        db: Database session
        current_user: Authenticated user

    Returns:
        Created graph data
    """
    try:
        # Create new graph with UUID generation
        new_graph = Graph(
            id=str(uuid.uuid4()),  # Generate UUID for the graph
            name=graph_data.get("name", "Untitled"),
            description=graph_data.get("description", ""),
            graph_data=graph_data.get("graph_data", {}),
            is_template=graph_data.get("is_template", False),
            user_id=current_user.id
        )

        db.add(new_graph)
        db.commit()
        db.refresh(new_graph)

        return {
            "success": True,
            "data": new_graph,
            "message": "Graph created successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create graph: {str(e)}"
        )


@router.put("/graphs/{graph_id}")
async def update_graph(
    graph_id: str,
    graph_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing graph.

    Args:
        graph_id: Graph identifier
        graph_data: Updated graph data
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated graph data
    """
    try:
        # Find existing graph
        graph = db.query(Graph).filter(
            Graph.id == graph_id,
            Graph.user_id == current_user.id
        ).first()

        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found"
            )

        # Update graph fields
        if "name" in graph_data:
            graph.name = graph_data["name"]
        if "description" in graph_data:
            graph.description = graph_data["description"]
        if "graph_data" in graph_data:
            graph.graph_data = graph_data["graph_data"]
        if "is_template" in graph_data:
            graph.is_template = graph_data["is_template"]

        db.commit()
        db.refresh(graph)

        return {
            "success": True,
            "data": graph,
            "message": "Graph updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update graph: {str(e)}"
        )


@router.delete("/graphs/{graph_id}")
async def delete_graph(
    graph_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a graph.

    Args:
        graph_id: Graph identifier
        db: Database session
        current_user: Authenticated user

    Returns:
        Success confirmation
    """
    try:
        # Find existing graph
        graph = db.query(Graph).filter(
            Graph.id == graph_id,
            Graph.user_id == current_user.id
        ).first()

        if not graph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Graph not found"
            )

        # Delete the graph
        db.delete(graph)
        db.commit()

        return {
            "success": True,
            "message": "Graph deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete graph: {str(e)}"
        )