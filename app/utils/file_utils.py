"""File utility functions."""
import hashlib
import re
from typing import BinaryIO, Tuple

import magic
from langchain_community.document_loaders import Blob
from langchain_community.document_loaders.parsers.generic import MimeTypeBasedParser
from langchain_community.document_loaders.parsers.html.bs4 import BS4HTMLParser
from langchain_community.document_loaders.parsers.msword import MsWordParser
from langchain_community.document_loaders.parsers.pdf import PDFMinerParser
from langchain_community.document_loaders.parsers.txt import TextParser

from app.core.logging import logger
from app.exceptions.custom_exceptions import (
    FileProcessingError,
    UnsupportedFileTypeError,
    FileSizeLimitError
)


class FileProcessor:
    """Utility class for file processing operations."""
    
    SUPPORTED_HANDLERS = {
        "application/pdf": PDFMinerParser(),
        "text/plain": TextParser(),
        "text/html": BS4HTMLParser(),
        "application/msword": MsWordParser(),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": MsWordParser()
    }
    
    def __init__(self, max_file_size_mb: int = 10):
        """Initialize file processor.
        
        Args:
            max_file_size_mb: Maximum file size in MB
        """
        self.max_file_size_mb = max_file_size_mb
        self.supported_mimetypes = sorted(self.SUPPORTED_HANDLERS.keys())
        self.parser = MimeTypeBasedParser(
            handlers=self.SUPPORTED_HANDLERS,
            fallback_parser=None
        )
        
        try:
            self.mime = magic.Magic(mime=True)
        except Exception as e:
            logger.error(f"Failed to initialize magic library: {str(e)}")
            raise FileProcessingError("Failed to initialize file type detection")
    
    def get_content_hash(self, content: bytes) -> str:
        """Generate SHA256 hash of content for caching.
        
        Args:
            content: File content as bytes
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content).hexdigest()
    
    def guess_mimetype(self, file_bytes: bytes) -> str:
        """Detect MIME type of file content.
        
        Args:
            file_bytes: File content as bytes
            
        Returns:
            MIME type string
            
        Raises:
            UnsupportedFileTypeError: If file type is not supported
            FileProcessingError: If detection fails
        """
        try:
            mime_type = self.mime.from_buffer(file_bytes)
            if mime_type not in self.supported_mimetypes:
                raise UnsupportedFileTypeError(
                    f"Unsupported file type: {mime_type}. "
                    f"Supported types: {', '.join(self.supported_mimetypes)}"
                )
            return mime_type
        except UnsupportedFileTypeError:
            raise
        except Exception as e:
            logger.error(f"Failed to detect MIME type: {str(e)}")
            raise FileProcessingError(f"Failed to detect file type: {str(e)}")
    
    def validate_file_size(self, content: bytes) -> None:
        """Validate file size against maximum limit.
        
        Args:
            content: File content as bytes
            
        Raises:
            FileSizeLimitError: If file exceeds size limit
        """
        size_mb = len(content) / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            raise FileSizeLimitError(
                f"File size ({size_mb:.2f}MB) exceeds maximum limit of "
                f"{self.max_file_size_mb}MB"
            )
    
    def extract_text_from_content(
        self,
        content: bytes,
        filename: str
    ) -> Tuple[str, str]:
        """Extract text from file content.
        
        Args:
            content: File content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, mime_type)
            
        Raises:
            FileProcessingError: If extraction fails
        """
        try:
            # Validate file size
            self.validate_file_size(content)
            
            # Detect MIME type
            mime_type = self.guess_mimetype(content)
            
            # Create blob for processing
            blob = Blob.from_data(
                data=content,
                path=filename,
                mime_type=mime_type
            )
            
            # Extract text
            documents = self.parser.parse(blob)
            extracted_text = "\n".join([doc.page_content for doc in documents])
            
            # Clean text
            cleaned_text = self.clean_text(extracted_text)
            
            logger.info(f"Successfully extracted text from {filename} ({mime_type})")
            return cleaned_text, mime_type
            
        except (UnsupportedFileTypeError, FileSizeLimitError):
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from {filename}: {str(e)}")
            raise FileProcessingError(f"Failed to process file: {str(e)}")
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extracted text by removing HTML tags and extra whitespace.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        
        # Remove multiple quotes
        text = re.sub(r'"+', '"', text)
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    def get_supported_formats(self) -> list:
        """Get list of supported MIME types.
        
        Returns:
            List of supported MIME types
        """
        return self.supported_mimetypes