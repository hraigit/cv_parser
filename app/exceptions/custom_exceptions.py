"""Custom exception classes."""
from typing import Optional


class BaseAPIException(Exception):
    """Base exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


# File Processing Exceptions
class FileProcessingError(BaseAPIException):
    """Exception for file processing errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="FILE_PROCESSING_ERROR")


class UnsupportedFileTypeError(BaseAPIException):
    """Exception for unsupported file types."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_code="UNSUPPORTED_FILE_TYPE")


class FileSizeLimitError(BaseAPIException):
    """Exception for file size limit exceeded."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=413, error_code="FILE_SIZE_LIMIT_EXCEEDED")


class BatchProcessingError(BaseAPIException):
    """Exception for batch processing errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="BATCH_PROCESSING_ERROR")


# OpenAI Exceptions
class OpenAIError(BaseAPIException):
    """Exception for OpenAI API errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="OPENAI_ERROR")


class OpenAIRateLimitError(BaseAPIException):
    """Exception for OpenAI rate limit errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=429, error_code="OPENAI_RATE_LIMIT")


class OpenAIInvalidResponseError(BaseAPIException):
    """Exception for invalid OpenAI responses."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="OPENAI_INVALID_RESPONSE")


# Parser Exceptions
class ParserError(BaseAPIException):
    """Exception for parser errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="PARSER_ERROR")


class EntityExtractionError(BaseAPIException):
    """Exception for entity extraction errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="ENTITY_EXTRACTION_ERROR")


# Database Exceptions
class DatabaseError(BaseAPIException):
    """Exception for database errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=500, error_code="DATABASE_ERROR")


class RecordNotFoundError(BaseAPIException):
    """Exception for record not found errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=404, error_code="RECORD_NOT_FOUND")


# Validation Exceptions
class ValidationError(BaseAPIException):
    """Exception for validation errors."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR")


class MissingRequiredFieldError(BaseAPIException):
    """Exception for missing required fields."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_code="MISSING_REQUIRED_FIELD")