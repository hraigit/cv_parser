"""CV data structure schemas (KVKK-compliant - no personal data)."""

from typing import List, Optional

from pydantic import BaseModel, Field


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
    has_driving_license: Optional[str] = Field(
        default="not_specified",
        description="Driving license status: 'yes', 'no', or 'not_specified' if not mentioned in CV",
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


class WorkDate(BaseModel):
    """Work experience date model."""

    year: Optional[str] = None
    month: Optional[str] = None

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
