"""
HTTP Exception classes for FastAPI endpoints
Provides standard HTTP exceptions with proper status codes
"""

from typing import Optional, Dict, Any

class HTTPException(Exception):
    """Base HTTP exception class"""
    
    def __init__(self, status_code: int, detail: str, headers: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)

class NotFoundError(HTTPException):
    """404 Not Found exception"""
    
    def __init__(self, detail: str = "Resource not found", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=404, detail=detail, headers=headers)

class ForbiddenError(HTTPException):
    """403 Forbidden exception"""
    
    def __init__(self, detail: str = "Access forbidden", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=403, detail=detail, headers=headers)

class UnauthorizedError(HTTPException):
    """401 Unauthorized exception"""
    
    def __init__(self, detail: str = "Authentication required", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, detail=detail, headers=headers)

class BadRequestError(HTTPException):
    """400 Bad Request exception"""
    
    def __init__(self, detail: str = "Bad request", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=400, detail=detail, headers=headers)

class ConflictError(HTTPException):
    """409 Conflict exception"""
    
    def __init__(self, detail: str = "Resource conflict", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=409, detail=detail, headers=headers) 