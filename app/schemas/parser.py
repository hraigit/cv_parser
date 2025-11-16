"""Parser API request/response schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AsyncJobResponse(BaseModel):
    """Response model for async job creation."""

    candidate_id: UUID = Field(
        ..., description="Candidate identifier (used as job ID for tracking)"
    )
    status: str = Field(default="processing", description="Initial job status")
    message: str = Field(
        default="Job created and processing in background", description="Status message"
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class JobStatusResponse(BaseModel):
    """Response model for job status polling."""

    candidate_id: UUID = Field(..., description="Candidate identifier (same as job ID)")
    status: str = Field(
        ..., description="Current job status: processing, success, failed"
    )
    file_name: Optional[str] = Field(None, description="File name if applicable")
    cv_language: Optional[str] = Field(None, description="Detected CV language")
    processing_time_seconds: Optional[float] = Field(
        None, description="Processing time if completed"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True
