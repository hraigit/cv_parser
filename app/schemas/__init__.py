"""Schemas package."""

from app.schemas.parser import (
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

__all__ = [
    # Advanced mode models
    "ParsedCVData",
    "CVProfile",
    "ProfileBasics",
    "Language",
    "Education",
    "TrainingCertification",
    "WorkDate",
    "ProfessionalExperience",
    "Award",
    # Basic mode models
    "BasicParsedCVData",
    "BasicCVProfile",
    "BasicEducation",
    "BasicTrainingCertification",
    "BasicProfessionalExperience",
    "BasicAward",
]
