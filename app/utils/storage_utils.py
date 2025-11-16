"""File storage utilities for persisting uploaded files."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID

from app.core.config import settings
from app.core.logging import logger


class FileStorageManager:
    """Manages file storage to disk with timestamp-based naming."""

    def __init__(self):
        """Initialize file storage manager."""
        self.storage_path = Path(settings.FILE_STORAGE_PATH)
        self.enabled = settings.FILE_STORAGE_ENABLED

        # Create storage directory if enabled
        if self.enabled:
            self._ensure_storage_directory()

    def _ensure_storage_directory(self) -> None:
        """Ensure storage directory exists."""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"File storage directory ready: {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {str(e)}")
            raise

    def generate_filename(
        self, original_filename: str, job_id: Optional[UUID] = None
    ) -> str:
        """Generate unique filename with timestamp.

        Format: {original_name}_{timestamp}_{job_id}.{extension}
        Example: resume_20251116_143022_550e8400.pdf

        Args:
            original_filename: Original file name
            job_id: Optional job UUID for tracking

        Returns:
            Unique filename with timestamp
        """
        # Get timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Parse original filename
        name_parts = original_filename.rsplit(".", 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
        else:
            base_name = original_filename
            extension = "bin"  # fallback

        # Clean base name (remove special characters)
        base_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in base_name)
        base_name = base_name[:50]  # Limit length

        # Build unique filename
        if job_id:
            job_id_short = str(job_id).split("-")[0]  # First segment of UUID
            unique_name = f"{base_name}_{timestamp}_{job_id_short}.{extension}"
        else:
            unique_name = f"{base_name}_{timestamp}.{extension}"

        return unique_name

    def save_file(
        self, file_content: bytes, original_filename: str, job_id: Optional[UUID] = None
    ) -> Optional[str]:
        """Save file to storage directory.

        Args:
            file_content: File content as bytes
            original_filename: Original filename
            job_id: Optional job UUID

        Returns:
            Full path to saved file, or None if storage disabled

        Raises:
            IOError: If file save fails
        """
        if not self.enabled:
            logger.debug("File storage disabled, skipping save")
            return None

        try:
            # Generate unique filename
            unique_filename = self.generate_filename(original_filename, job_id)
            file_path = self.storage_path / unique_filename

            # Write file
            with open(file_path, "wb") as f:
                f.write(file_content)

            logger.info(
                f"File saved to storage: {file_path} "
                f"(size: {len(file_content)} bytes, job_id: {job_id})"
            )

            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to save file {original_filename}: {str(e)}")
            raise IOError(f"Failed to save file: {str(e)}")

    def get_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file from storage.

        Args:
            file_path: Full path to file

        Returns:
            File content as bytes, or None if not found
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File not found: {file_path}")
                return None

            with open(path, "rb") as f:
                content = f.read()

            logger.debug(f"Retrieved file from storage: {file_path}")
            return content

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """Delete file from storage.

        Args:
            file_path: Full path to file

        Returns:
            True if deleted, False if not found or error
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File not found for deletion: {file_path}")
                return False

            path.unlink()
            logger.info(f"Deleted file from storage: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False

    def get_storage_stats(self) -> dict:
        """Get storage directory statistics.

        Returns:
            Dictionary with storage stats
        """
        if not self.enabled:
            return {"enabled": False, "message": "File storage is disabled"}

        try:
            files = list(self.storage_path.glob("*"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())

            return {
                "enabled": True,
                "storage_path": str(self.storage_path),
                "total_files": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {"enabled": True, "error": str(e)}


# Global instance
_file_storage_manager: Optional[FileStorageManager] = None


def get_file_storage_manager() -> FileStorageManager:
    """Get singleton file storage manager instance."""
    global _file_storage_manager
    if _file_storage_manager is None:
        _file_storage_manager = FileStorageManager()
    return _file_storage_manager
