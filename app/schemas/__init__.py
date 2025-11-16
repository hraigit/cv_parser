"""Schemas package."""

# CV data structure schemas
from app.schemas.cv_schemas import (
    Award,
    BasicAward,
    BasicCVProfile,
    BasicEducation,
    BasicParsedCVData,
    BasicProfessionalExperience,
    BasicTrainingCertification,
    CVProfile,
    Education,
    Language,
    ParsedCVData,
    ProfessionalExperience,
    ProfileBasics,
    TrainingCertification,
    WorkDate,
)

# API request/response schemas
from app.schemas.parser import AsyncJobResponse, JobStatusResponse

__all__ = [
    # CV data structures
    "Award",
    "BasicAward",
    "BasicCVProfile",
    "BasicEducation",
    "BasicParsedCVData",
    "BasicProfessionalExperience",
    "BasicTrainingCertification",
    "CVProfile",
    "Education",
    "Language",
    "ParsedCVData",
    "ProfessionalExperience",
    "ProfileBasics",
    "TrainingCertification",
    "WorkDate",
    # API schemas (actively used)
    "AsyncJobResponse",
    "JobStatusResponse",
]
