"""Parser schemas for CV/Entity extraction."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import TimestampMixin


# Request Schemas
class ParseTextRequest(BaseModel):
    """Request model for parsing text input (supports both formatted CV and free-form text)."""

    user_id: str = Field(..., min_length=1, description="User identifier")
    session_id: str = Field(..., min_length=1, description="Session identifier")
    text: str = Field(
        ...,
        min_length=10,
        description="CV text to parse (formatted resume or free-form self-description)",
    )


class ParseFileRequest(BaseModel):
    """Request model for parsing file input (form data)."""

    user_id: str = Field(..., min_length=1, description="User identifier")
    session_id: str = Field(..., min_length=1, description="Session identifier")


# CV Structure Schemas (KVKK-compliant - no personal data)
class ProfileBasics(BaseModel):
    """Basic profile information (KVKK-compliant - no personal identifiers)."""

    profession: Optional[str] = Field(None, description="Primary profession or role")
    summary: Optional[str] = Field(
        None,
        description="Professional summary WITHOUT personal information or names",
    )
    skills: List[str] = Field(
        default_factory=list, description="List of professional skills"
    )
    has_driving_license: bool = Field(
        default=False, description="Whether candidate has driving license"
    )
    total_experience_in_years: Optional[float] = Field(
        None, description="Total years of professional experience (calculated)"
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"  # Ignore extra fields from OpenAI


class Language(BaseModel):
    """Language proficiency model."""

    name: Optional[str] = None
    iso_code: Optional[str] = None
    fluency: Optional[str] = None

    class Config:
        """Pydantic config."""

        extra = "ignore"


class Education(BaseModel):
    """Education model."""

    start_year: Optional[str] = None
    is_current: bool = False
    end_year: Optional[str] = None
    issuing_organization: Optional[str] = None
    description: Optional[str] = None
    duration_in_years: Optional[int] = Field(
        None, description="Duration in years (calculated)"
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"


class TrainingCertification(BaseModel):
    """Training and certification model."""

    year: Optional[str] = None
    issuing_organization: Optional[str] = None
    description: Optional[str] = None

    class Config:
        """Pydantic config."""

        extra = "ignore"


class WorkDate(BaseModel):
    """Work experience date model."""

    year: Optional[str] = None
    month: Optional[str] = None

    class Config:
        """Pydantic config."""

        extra = "ignore"


class ProfessionalExperience(BaseModel):
    """Professional experience model."""

    start_date: Optional[WorkDate] = None
    is_current: bool = False
    end_date: Optional[WorkDate] = None
    company: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration_in_months: Optional[int] = Field(
        None, description="Duration in months (calculated)"
    )

    class Config:
        """Pydantic config."""

        extra = "ignore"


class Award(BaseModel):
    """Award model."""

    year: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None

    class Config:
        """Pydantic config."""

        extra = "ignore"


# ADVANCED MODE - Full CV Profile with all details
class CVProfile(BaseModel):
    """CV profile model (KVKK-compliant - no references section) - ADVANCED MODE with full details."""

    basics: ProfileBasics
    languages: List[Language] = Field(default_factory=list)
    educations: List[Education] = Field(default_factory=list)
    trainings_and_certifications: List[TrainingCertification] = Field(
        default_factory=list
    )
    professional_experiences: List[ProfessionalExperience] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        extra = "ignore"


# BASIC MODE - Simplified nested models without descriptions
class BasicEducation(BaseModel):
    """Basic education model - high-level info only."""

    start_year: Optional[str] = None
    is_current: bool = False
    end_year: Optional[str] = None
    issuing_organization: Optional[str] = None
    duration_in_years: Optional[int] = Field(
        None, description="Duration in years (calculated)"
    )
    # description removed for basic mode

    class Config:
        """Pydantic config."""

        extra = "ignore"


class BasicTrainingCertification(BaseModel):
    """Basic training and certification model - high-level info only."""

    year: Optional[str] = None
    issuing_organization: Optional[str] = None
    # description removed for basic mode

    class Config:
        """Pydantic config."""

        extra = "ignore"


class BasicProfessionalExperience(BaseModel):
    """Basic professional experience model - no detailed descriptions."""

    start_date: Optional[WorkDate] = None
    is_current: bool = False
    end_date: Optional[WorkDate] = None
    company: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    duration_in_months: Optional[int] = Field(
        None, description="Duration in months (calculated)"
    )
    # description removed for basic mode

    class Config:
        """Pydantic config."""

        extra = "ignore"


class BasicAward(BaseModel):
    """Basic award model - title only."""

    year: Optional[str] = None
    title: Optional[str] = None
    # description removed for basic mode

    class Config:
        """Pydantic config."""

        extra = "ignore"


# BASIC MODE - Simplified CV Profile without descriptions
class BasicCVProfile(BaseModel):
    """Basic CV profile model - high-level information only, no detailed descriptions."""

    basics: ProfileBasics  # Uses same ProfileBasics but with short summary
    languages: List[Language] = Field(default_factory=list)  # Same as advanced
    educations: List[BasicEducation] = Field(default_factory=list)
    trainings_and_certifications: List[BasicTrainingCertification] = Field(
        default_factory=list
    )
    professional_experiences: List[BasicProfessionalExperience] = Field(
        default_factory=list
    )
    awards: List[BasicAward] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        extra = "ignore"


class ParsedCVData(BaseModel):
    """Complete parsed CV data structure - ADVANCED MODE."""

    profile: CVProfile
    cv_language: Optional[str] = None

    class Config:
        """Pydantic config."""

        extra = "ignore"


class BasicParsedCVData(BaseModel):
    """Basic parsed CV data structure - BASIC MODE."""

    profile: BasicCVProfile
    cv_language: Optional[str] = None

    class Config:
        """Pydantic config."""

        extra = "ignore"


# Response Schemas
class ParseResponse(TimestampMixin):
    """Response model for parse operations."""

    id: UUID = Field(..., description="Parse result ID")
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    parsed_data: ParsedCVData = Field(..., description="Parsed CV data")
    cv_language: Optional[str] = Field(None, description="Detected CV language")
    file_name: Optional[str] = Field(None, description="Original file name")
    processing_time_seconds: Optional[float] = Field(
        None, description="Processing time"
    )
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


class AsyncJobResponse(BaseModel):
    """Response model for async job creation."""

    job_id: UUID = Field(..., description="Job identifier for tracking")
    status: str = Field(default="processing", description="Initial job status")
    message: str = Field(
        default="Job created and processing in background", description="Status message"
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class JobStatusResponse(BaseModel):
    """Response model for job status polling."""

    job_id: UUID = Field(..., description="Job identifier")
    status: str = Field(
        ..., description="Current job status: processing, success, failed"
    )
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
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
