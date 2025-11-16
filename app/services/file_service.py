"""File service with caching and async processing."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

from cachetools import TTLCache
from fastapi import UploadFile

from app.core.config import settings
from app.core.logging import logger
from app.exceptions.custom_exceptions import FileProcessingError
from app.utils.file_utils import FileProcessor


class FileService:
    """Async-safe singleton file service with caching."""

    _instance: Optional["FileService"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize file service only once."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True

        # Initialize file processor
        self.file_processor = FileProcessor(max_file_size_mb=settings.MAX_FILE_SIZE_MB)

        # Initialize thread pool for blocking I/O
        self.thread_pool = ThreadPoolExecutor(
            max_workers=settings.MAX_WORKERS, thread_name_prefix="file_service_worker"
        )

        # Initialize cache
        self.cache = TTLCache(
            maxsize=settings.CACHE_MAX_SIZE, ttl=settings.CACHE_TTL_SECONDS
        )

        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0

        logger.info("File service initialized successfully")

    async def extract_text_from_file(self, file: UploadFile) -> Dict[str, Any]:
        """Extract text from uploaded file with caching.

        Args:
            file: Uploaded file

        Returns:
            Dictionary containing extracted text and metadata

        Raises:
            FileProcessingError: If extraction fails
        """
        start_time = time.time()

        try:
            # Read file content
            content = await file.read()
            await file.seek(0)  # Reset file pointer

            # Generate cache key
            content_hash = self.file_processor.get_content_hash(content)

            # Check cache
            if content_hash in self.cache:
                self._cache_hits += 1
                logger.info(f"Cache hit for file: {file.filename}")
                cached_result = self.cache[content_hash]
                cached_result["from_cache"] = True
                return cached_result

            self._cache_misses += 1

            # Process file in thread pool
            loop = asyncio.get_event_loop()
            filename = file.filename or "unknown"
            extracted_text, mime_type = await loop.run_in_executor(
                self.thread_pool,
                self.file_processor.extract_text_from_content,
                content,
                filename,
            )

            # Check if it's an image (empty text indicates vision processing needed)
            is_image = self.file_processor.is_image_format(mime_type)

            # Prepare response
            processing_time = time.time() - start_time
            result = {
                "content": extracted_text,
                "filename": file.filename,
                "mime_type": mime_type,
                "content_length": len(extracted_text),
                "processing_time_seconds": processing_time,
                "from_cache": False,
                "is_image": is_image,  # Flag for vision processing
                "raw_bytes": (
                    content if is_image else None
                ),  # Store bytes for vision API
            }

            # Update cache (but don't cache raw bytes for images)
            cache_result = result.copy()
            if is_image:
                cache_result["raw_bytes"] = None  # Don't cache large image data
            self.cache[content_hash] = cache_result

            logger.info(
                f"Successfully processed file: {file.filename} "
                f"({'IMAGE - Vision API required' if is_image else 'TEXT extracted'}) "
                f"in {processing_time:.2f}s"
            )

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Failed to process file {file.filename} "
                f"after {processing_time:.2f}s: {str(e)}"
            )
            raise FileProcessingError(f"Failed to process file: {str(e)}")

    async def extract_text_from_content(
        self, content: bytes, filename: str
    ) -> Dict[str, Any]:
        """Extract text from raw content.

        Args:
            content: File content as bytes
            filename: Original filename

        Returns:
            Dictionary containing extracted text and metadata
        """
        start_time = time.time()

        try:
            # Process in thread pool
            loop = asyncio.get_event_loop()
            extracted_text, mime_type = await loop.run_in_executor(
                self.thread_pool,
                self.file_processor.extract_text_from_content,
                content,
                filename,
            )

            # Check if it's an image
            is_image = self.file_processor.is_image_format(mime_type)

            processing_time = time.time() - start_time

            return {
                "content": extracted_text,
                "filename": filename,
                "mime_type": mime_type,
                "content_length": len(extracted_text),
                "processing_time_seconds": processing_time,
                "is_image": is_image,
                "raw_bytes": content if is_image else None,
            }

        except Exception as e:
            logger.error(f"Failed to extract text: {str(e)}")
            raise FileProcessingError(f"Failed to extract text: {str(e)}") from e

    def get_supported_formats(self) -> list:
        """Get list of supported file formats.

        Returns:
            List of supported MIME types
        """
        return self.file_processor.get_supported_formats()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (
            (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "size": len(self.cache),
            "max_size": self.cache.maxsize,
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
        }

    async def cleanup(self):
        """Cleanup resources."""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
        self.cache.clear()
        logger.info("File service cleaned up")


def get_file_service() -> FileService:
    """Get singleton file service instance."""
    return FileService()


# Global instance
file_service = get_file_service()
