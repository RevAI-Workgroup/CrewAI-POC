"""
Tool Repository Service for CrewAI Backend
Manages CRUD operations for tools
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.tool import Tool
from schemas.tool import ToolCreate, ToolUpdate
from exceptions.http_exceptions import NotFoundError, ForbiddenError

class ToolRepository:
    """Repository service for tool CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tool(self, tool_data: ToolCreate, user_id: str) -> Tool:
        """Create a new tool"""
        tool = Tool(
            name=tool_data.name,
            description=tool_data.description,
            schema=tool_data.schema,
            implementation=tool_data.implementation,
            version=tool_data.version,
            category=tool_data.category,
            tags=tool_data.tags,
            is_public="true" if tool_data.is_public else "false",
            user_id=user_id
        )
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        return tool
    
    def get_tool_by_id(self, tool_id: int, user_id: Optional[str] = None) -> Tool:
        """Get tool by ID with optional user access check"""
        query = self.db.query(Tool).filter(Tool.id == tool_id)
        
        if user_id:
            # User can access their own tools or public tools
            query = query.filter(
                or_(
                    Tool.user_id == user_id,
                    Tool.is_public == "true"
                )
            )
        
        tool = query.first()
        if not tool:
            raise NotFoundError(f"Tool with ID {tool_id} not found")
        
        return tool
    
    def get_tools_by_user(
        self, 
        user_id: str, 
        include_public: bool = True,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Tool], int]:
        """Get tools for a user with filtering and pagination"""
        query = self.db.query(Tool)
        
        # Filter by user or public tools
        if include_public:
            query = query.filter(
                or_(
                    Tool.user_id == user_id,
                    Tool.is_public == "true"
                )
            )
        else:
            query = query.filter(Tool.user_id == user_id)
        
        # Filter by category
        if category:
            query = query.filter(Tool.category == category)
        
        # Search in name and description
        if search:
            search_filter = or_(
                Tool.name.ilike(f"%{search}%"),
                Tool.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        tools = query.offset(offset).limit(page_size).all()
        
        return tools, total
    
    def update_tool(self, tool_id: int, tool_data: ToolUpdate, user_id: str) -> Tool:
        """Update an existing tool"""
        tool = self.db.query(Tool).filter(
            and_(Tool.id == tool_id, Tool.user_id == user_id)
        ).first()
        
        if not tool:
            raise NotFoundError(f"Tool with ID {tool_id} not found or access denied")
        
        # Update fields that are provided
        update_data = tool_data.model_dump(exclude_unset=True)
        
        # Convert is_public boolean to string
        if "is_public" in update_data:
            update_data["is_public"] = "true" if update_data["is_public"] else "false"
        
        for field, value in update_data.items():
            setattr(tool, field, value)
        
        self.db.commit()
        self.db.refresh(tool)
        return tool
    
    def delete_tool(self, tool_id: int, user_id: str) -> bool:
        """Delete a tool"""
        tool = self.db.query(Tool).filter(
            and_(Tool.id == tool_id, Tool.user_id == user_id)
        ).first()
        
        if not tool:
            raise NotFoundError(f"Tool with ID {tool_id} not found or access denied")
        
        self.db.delete(tool)
        self.db.commit()
        return True
    
    def get_public_tools(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[Tool], int]:
        """Get public tools with filtering and pagination"""
        query = self.db.query(Tool).filter(Tool.is_public == "true")
        
        # Filter by category
        if category:
            query = query.filter(Tool.category == category)
        
        # Search in name and description
        if search:
            search_filter = or_(
                Tool.name.ilike(f"%{search}%"),
                Tool.description.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        tools = query.offset(offset).limit(page_size).all()
        
        return tools, total
    
    def get_tool_categories(self) -> List[str]:
        """Get all available tool categories"""
        categories = (
            self.db.query(Tool.category)
            .filter(Tool.category.isnot(None))
            .distinct()
            .all()
        )
        return [cat[0] for cat in categories if cat[0]] 