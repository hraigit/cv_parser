"""Common schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model."""
    
    success: bool = Field(..., description="Operation success status")
    message: Optional[str] = Field(None, description="Response message")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True