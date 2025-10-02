# app/__init__.py
"""CV Parser Application Package."""
__version__ = "1.0.0"

# app/core/__init__.py
"""Core application components."""
from app.core.config import settings, get_settings
from app.core.database import db_manager, get_db, Base
from app.core.logging import logger, get_logger

__all__ = [
    "settings",
    "get_settings",
    "db_manager",
    "get_db",
    "Base",
    "logger",
    "get_logger",
]

# app/models/__init__.py
"""Database models."""
from app.models.parser import ParsedCV

__all__ = ["ParsedCV"]

# app/schemas/__init__.py
"""Pydantic schemas."""
from app.schemas.common import (
    BaseResponse,
    ErrorResponse,
    HealthResponse,
    PaginationParams,
)
from app.schemas.parser import (
    ParseTextRequest,
    ParseFileRequest,
    ParseResponse,
    ParsedCVData,
    ParseHistoryResponse,
    ParseStatusResponse,
)

__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "HealthResponse",
    "PaginationParams",
    "ParseTextRequest",
    "ParseFileRequest",
    "ParseResponse",
    "ParsedCVData",
    "ParseHistoryResponse",
    "ParseStatusResponse",
]

# app/repositories/__init__.py
"""Database repositories."""
from app.repositories.parser_repository import (
    ParserRepository,
    get_parser_repository,
)

__all__ = ["ParserRepository", "get_parser_repository"]

# app/services/__init__.py
"""Business logic services."""
from app.services.file_service import FileService, get_file_service
from app.services.openai_service import OpenAIService, get_openai_service
from app.services.parser_service import ParserService, get_parser_service

__all__ = [
    "FileService",
    "get_file_service",
    "OpenAIService",
    "get_openai_service",
    "ParserService",
    "get_parser_service",
]

# app/utils/__init__.py
"""Utility functions."""
from app.utils.file_utils import FileProcessor
from app.utils.text_utils import (
    truncate_text,
    normalize_whitespace,
    extract_emails,
    extract_phone_numbers,
    detect_language,
    sanitize_filename,
)

__all__ = [
    "FileProcessor",
    "truncate_text",
    "normalize_whitespace",
    "extract_emails",
    "extract_phone_numbers",
    "detect_language",
    "sanitize_filename",
]

# app/exceptions/__init__.py
"""Custom exceptions."""
from app.exceptions.custom_exceptions import (
    BaseAPIException,
    FileProcessingError,
    UnsupportedFileTypeError,
    FileSizeLimitError,
    BatchProcessingError,
    OpenAIError,
    OpenAIRateLimitError,
    OpenAIInvalidResponseError,
    ParserError,
    EntityExtractionError,
    DatabaseError,
    RecordNotFoundError,
    ValidationError,
    MissingRequiredFieldError,
)

__all__ = [
    "BaseAPIException",
    "FileProcessingError",
    "UnsupportedFileTypeError",
    "FileSizeLimitError",
    "BatchProcessingError",
    "OpenAIError",
    "OpenAIRateLimitError",
    "OpenAIInvalidResponseError",
    "ParserError",
    "EntityExtractionError",
    "DatabaseError",
    "RecordNotFoundError",
    "ValidationError",
    "MissingRequiredFieldError",
]

# app/api/__init__.py
"""API package."""

# app/api/v1/__init__.py
"""API v1 package."""

# app/api/v1/routes/__init__.py
"""API v1 routes."""