"""Parser schemas for CV/Entity extraction."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import TimestampMixin


# Request Schemas
class ParseTextRequest(BaseModel):
    """Request model for parsing text input."""
    
    user_id: str = Field(..., min_length=1, description="User identifier")
    session_id: str = Field(..., min_length=1, description="Session identifier")
    text: str = Field(..., min_length=10, description="Text to parse")


class ParseFreeTextRequest(BaseModel):
    """Request model for parsing free-form text where candidate describes themselves."""
    
    user_id: str = Field(..., min_length=1, description="User identifier")
    session_id: str = Field(..., min_length=1, description="Session identifier")
    free_text: str = Field(..., min_length=20, description="Free-form text where candidate describes themselves")


class ParseFileRequest(BaseModel):
    """Request model for parsing file input (form data)."""
    
    user_id: str = Field(..., min_length=1, description="User identifier")
    session_id: str = Field(..., min_length=1, description="Session identifier")


# CV Structure Schemas (based on your prompt)
class DateOfBirth(BaseModel):
    """Date of birth model."""
    year: Optional[str] = None
    month: Optional[str] = None
    day: Optional[str] = None


class ProfileBasics(BaseModel):
    """Basic profile information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    urls: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    date_of_birth: Optional[DateOfBirth] = None
    address: Optional[str] = None
    total_experience_in_years: Optional[str] = None
    profession: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    has_driving_license: bool = False


class Language(BaseModel):
    """Language proficiency model."""
    name: Optional[str] = None
    iso_code: Optional[str] = None
    fluency: Optional[str] = None


class Education(BaseModel):
    """Education model."""
    start_year: Optional[str] = None
    is_current: bool = False
    end_year: Optional[str] = None
    issuing_organization: Optional[str] = None
    description: Optional[str] = None


class TrainingCertification(BaseModel):
    """Training and certification model."""
    year: Optional[str] = None
    issuing_organization: Optional[str] = None
    description: Optional[str] = None


class WorkDate(BaseModel):
    """Work experience date model."""
    year: Optional[str] = None
    month: Optional[str] = None


class ProfessionalExperience(BaseModel):
    """Professional experience model."""
    start_date: Optional[WorkDate] = None
    is_current: bool = False
    end_date: Optional[WorkDate] = None
    duration_in_months: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class Award(BaseModel):
    """Award model."""
    year: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class Reference(BaseModel):
    """Reference model."""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    description: Optional[str] = None


class CVProfile(BaseModel):
    """CV profile model."""
    basics: ProfileBasics
    languages: List[Language] = Field(default_factory=list)
    educations: List[Education] = Field(default_factory=list)
    trainings_and_certifications: List[TrainingCertification] = Field(default_factory=list)
    professional_experiences: List[ProfessionalExperience] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)


class ParsedCVData(BaseModel):
    """Complete parsed CV data structure."""
    profile: CVProfile
    cv_language: Optional[str] = None


# Response Schemas
class ParseResponse(TimestampMixin):
    """Response model for parse operations."""
    
    id: UUID = Field(..., description="Parse result ID")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    parsed_data: ParsedCVData = Field(..., description="Parsed CV data")
    cv_language: Optional[str] = Field(None, description="Detected CV language")
    file_name: Optional[str] = Field(None, description="Original file name")
    processing_time_seconds: Optional[float] = Field(None, description="Processing time")
    status: str = Field(..., description="Processing status")
    

class ParseHistoryResponse(BaseModel):
    """Response model for parse history."""
    
    items: List[ParseResponse]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        return (self.total + self.page_size - 1) // self.page_size


class ParseStatusResponse(BaseModel):
    """Response for parse status check."""
    
    id: UUID
    status: str
    user_id: str
    session_id: str
    created_at: datetime
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True