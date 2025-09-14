from typing import Any, Dict, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    """Base API response model"""

    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel):
    """Paginated response model"""

    success: bool = True
    data: list
    pagination: Dict[str, Any]
    message: Optional[str] = None
