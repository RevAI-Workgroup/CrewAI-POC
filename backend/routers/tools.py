"""
Tools Router for CrewAI Backend API
Provides CRUD endpoints for tool management
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from utils.dependencies import get_db, get_current_user
from models.user import User
from schemas.tool import (
    ToolCreate, ToolUpdate, ToolResponse, ToolListResponse,
    ToolExecuteRequest, ToolExecuteResponse
)
from services.tool_repository import ToolRepository
from services.tool_executor import ToolExecutor
from exceptions.http_exceptions import NotFoundError, ForbiddenError

router = APIRouter(prefix="/tools", tags=["tools"])

@router.post("/", response_model=ToolResponse)
async def create_tool(
    tool_data: ToolCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tool"""
    try:
        tool_repo = ToolRepository(db)
        tool = tool_repo.create_tool(tool_data, str(current_user.id))
        return ToolResponse.model_validate(tool)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=ToolListResponse)
async def list_tools(
    include_public: bool = Query(True, description="Include public tools"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List tools for the current user"""
    try:
        tool_repo = ToolRepository(db)
        tools, total = tool_repo.get_tools_by_user(
            user_id=str(current_user.id),
            include_public=include_public,
            category=category,
            search=search,
            page=page,
            page_size=page_size
        )
        
        tool_responses = [ToolResponse.model_validate(tool) for tool in tools]
        return ToolListResponse(
            tools=tool_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/public", response_model=ToolListResponse)
async def list_public_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """List public tools (no authentication required)"""
    try:
        tool_repo = ToolRepository(db)
        tools, total = tool_repo.get_public_tools(
            category=category,
            search=search,
            page=page,
            page_size=page_size
        )
        
        tool_responses = [ToolResponse.model_validate(tool) for tool in tools]
        return ToolListResponse(
            tools=tool_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories", response_model=List[str])
async def get_tool_categories(db: Session = Depends(get_db)):
    """Get all available tool categories"""
    try:
        tool_repo = ToolRepository(db)
        categories = tool_repo.get_tool_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific tool by ID"""
    try:
        tool_repo = ToolRepository(db)
        tool = tool_repo.get_tool_by_id(tool_id, str(current_user.id))
        return ToolResponse.model_validate(tool)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    tool_data: ToolUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing tool"""
    try:
        tool_repo = ToolRepository(db)
        tool = tool_repo.update_tool(tool_id, tool_data, str(current_user.id))
        return ToolResponse.model_validate(tool)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a tool"""
    try:
        tool_repo = ToolRepository(db)
        tool_repo.delete_tool(tool_id, str(current_user.id))
        return {"message": "Tool deleted successfully"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/{tool_id}", response_model=ToolExecuteResponse)
async def execute_custom_tool(
    tool_id: int,
    request: ToolExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a custom tool by ID"""
    try:
        tool_executor = ToolExecutor(db)
        result = tool_executor.execute_custom_tool(
            tool_id=tool_id,
            parameters=request.parameters,
            user_id=str(current_user.id)
        )
        
        return ToolExecuteResponse(
            success=result.success,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/builtin/{tool_name}", response_model=ToolExecuteResponse)
async def execute_builtin_tool(
    tool_name: str,
    request: ToolExecuteRequest,
    db: Session = Depends(get_db)
):
    """Execute a built-in tool by name"""
    try:
        tool_executor = ToolExecutor(db)
        result = tool_executor.execute_builtin_tool(
            tool_name=tool_name,
            parameters=request.parameters
        )
        
        return ToolExecuteResponse(
            success=result.success,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 