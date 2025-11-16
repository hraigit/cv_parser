"""Parser service - business logic layer."""

import time
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_manager
from app.core.logging import logger
from app.exceptions.custom_exceptions import (
    EntityExtractionError,
    ParserError,
    ValidationError,
)
from app.repositories.parser_repository import get_parser_repository
from app.schemas.parser import ParsedCVData
from app.services.file_service import get_file_service
from app.services.openai_service import get_openai_service
from app.utils.storage_utils import get_file_storage_manager


class ParserService:
    """Service for CV/Entity parsing operations."""

    def __init__(self):
        """Initialize parser service."""
        self.file_service = get_file_service()
        self.openai_service = get_openai_service()
        self.repository = get_parser_repository()
        self.storage_manager = get_file_storage_manager()

    async def parse_from_text(
        self, session: AsyncSession, user_id: str, session_id: str, text: str
    ) -> Dict[str, Any]:
        """Parse CV from text input.

        Args:
            session: Database session
            user_id: User identifier
            session_id: Session identifier
            text: CV text to parse

        Returns:
            Parsed CV data with metadata

        Raises:
            ParserError: If parsing fails
        """
        start_time = time.time()

        try:
            logger.info(
                f"🚀 [TIMING] Starting text parsing for user: {user_id}, "
                f"session: {session_id}, text length: {len(text)} characters"
            )

            # Validate input
            if not text or len(text.strip()) < 10:
                raise ValidationError("Text is too short to parse")

            # Parse with OpenAI
            openai_start = time.time()
            parsed_result = await self.openai_service.parse_cv(text)
            openai_time = time.time() - openai_start

            logger.info(
                f"⏱️ [TIMING] OpenAI parsing completed in {openai_time:.2f} seconds"
            )

            # Extract metadata
            metadata = parsed_result.pop("_metadata", {})

            # Get CV language from parsed data
            cv_language = parsed_result.get("cv_language")

            # Calculate processing time
            processing_time = time.time() - start_time

            # Save to database
            db_start = time.time()
            db_record = await self.repository.create(
                session=session,
                user_id=user_id,
                session_id=session_id,
                parsed_data=parsed_result,
                input_text=text[:5000],  # Store first 5000 chars
                cv_language=cv_language,
                processing_time_seconds=processing_time,
                openai_model=metadata.get("model"),
                tokens_used=metadata.get("tokens_used"),
                status="success",
            )
            db_time = time.time() - db_start

            logger.info(
                f"✅ [TIMING] Successfully parsed text for user: {user_id}, "
                f"session: {session_id}, record_id: {db_record.id} | "
                f"Total: {processing_time:.2f}s, OpenAI: {openai_time:.2f}s, DB: {db_time:.2f}s"
            )

            return {
                "id": db_record.id,
                "user_id": user_id,
                "session_id": session_id,
                "parsed_data": parsed_result,
                "cv_language": cv_language,
                "processing_time_seconds": processing_time,
                "tokens_used": metadata.get("tokens_used"),
                "status": "success",
                "created_at": db_record.created_at,
            }

        except ValidationError:
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Failed to parse text for user: {user_id}, "
                f"session: {session_id}: {str(e)}"
            )

            # Save error to database
            try:
                await self.repository.create(
                    session=session,
                    user_id=user_id,
                    session_id=session_id,
                    parsed_data={},
                    input_text=text[:5000],
                    processing_time_seconds=processing_time,
                    status="failed",
                    error_message=str(e),
                )
            except Exception as db_error:
                logger.error(f"Failed to save error record: {str(db_error)}")

            raise ParserError(f"Failed to parse CV from text: {str(e)}")

    async def parse_from_file(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        file: UploadFile,
        parse_mode: str = "advanced",
    ) -> Dict[str, Any]:
        """Parse CV from uploaded file.

        Args:
            session: Database session
            user_id: User identifier
            session_id: Session identifier
            file: Uploaded file
            parse_mode: Parsing mode - "basic" for high-level info only, "advanced" for full details

        Returns:
            Parsed CV data with metadata

        Raises:
            ParserError: If parsing fails
        """
        start_time = time.time()

        try:
            logger.info(
                f"🚀 [TIMING] Starting file parsing for user: {user_id}, "
                f"session: {session_id}, file: {file.filename}, mode: {parse_mode}"
            )

            # Extract text from file
            file_start = time.time()
            extraction_result = await self.file_service.extract_text_from_file(file)
            extracted_text = extraction_result["content"]
            file_time = time.time() - file_start

            logger.info(
                f"📄 [TIMING] File extraction completed in {file_time:.2f} seconds"
            )

            # Validate extracted text
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise ValidationError("Extracted text is too short to parse")

            # Parse with OpenAI using specified mode
            openai_start = time.time()
            parsed_result = await self.openai_service.parse_cv(
                extracted_text, parse_mode=parse_mode
            )
            openai_time = time.time() - openai_start

            logger.info(
                f"⏱️ [TIMING] OpenAI parsing completed in {openai_time:.2f} seconds"
            )

            # Extract metadata
            metadata = parsed_result.pop("_metadata", {})

            # Get CV language
            cv_language = parsed_result.get("cv_language")

            # Calculate total processing time
            processing_time = time.time() - start_time

            # Save to database
            db_start = time.time()
            db_record = await self.repository.create(
                session=session,
                user_id=user_id,
                session_id=session_id,
                parsed_data=parsed_result,
                input_text=extracted_text[:5000],
                file_name=file.filename,
                file_mime_type=extraction_result["mime_type"],
                cv_language=cv_language,
                processing_time_seconds=processing_time,
                openai_model=metadata.get("model"),
                tokens_used=metadata.get("tokens_used"),
                status="success",
            )
            db_time = time.time() - db_start

            logger.info(
                f"✅ [TIMING] Successfully parsed file for user: {user_id}, "
                f"session: {session_id}, record_id: {db_record.id}, mode: {parse_mode} | "
                f"Total: {processing_time:.2f}s, File: {file_time:.2f}s, "
                f"OpenAI: {openai_time:.2f}s, DB: {db_time:.2f}s"
            )

            return {
                "id": db_record.id,
                "user_id": user_id,
                "session_id": session_id,
                "parsed_data": parsed_result,
                "cv_language": cv_language,
                "file_name": file.filename,
                "file_mime_type": extraction_result["mime_type"],
                "processing_time_seconds": processing_time,
                "tokens_used": metadata.get("tokens_used"),
                "parse_mode": parse_mode,
                "status": "success",
                "created_at": db_record.created_at,
            }

        except ValidationError:
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Failed to parse file for user: {user_id}, "
                f"session: {session_id}, file: {file.filename}: {str(e)}"
            )

            # Save error to database
            try:
                await self.repository.create(
                    session=session,
                    user_id=user_id,
                    session_id=session_id,
                    parsed_data={},
                    file_name=file.filename,
                    processing_time_seconds=processing_time,
                    status="failed",
                    error_message=str(e),
                )
            except Exception as db_error:
                logger.error(f"Failed to save error record: {str(db_error)}")

            raise ParserError(f"Failed to parse CV from file: {str(e)}")

    async def get_parse_result(
        self, session: AsyncSession, record_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get parse result by ID.

        Args:
            session: Database session
            record_id: Record UUID

        Returns:
            Parse result or None
        """
        try:
            db_record = await self.repository.get_by_id(session, record_id)

            if not db_record:
                return None

            return {
                "id": db_record.id,
                "user_id": db_record.user_id,
                "session_id": db_record.session_id,
                "parsed_data": db_record.parsed_data,
                "cv_language": db_record.cv_language,
                "file_name": db_record.file_name,
                "processing_time_seconds": db_record.processing_time_seconds,
                "status": db_record.status,
                "error_message": db_record.error_message,
                "created_at": db_record.created_at,
                "updated_at": db_record.updated_at,
            }

        except Exception as e:
            logger.error(f"Failed to get parse result {record_id}: {str(e)}")
            raise ParserError(f"Failed to retrieve parse result: {str(e)}")

    async def get_user_history(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        """Get parsing history for user.

        Args:
            session: Database session
            user_id: User identifier
            session_id: Optional session filter
            page: Page number
            page_size: Items per page

        Returns:
            History with pagination
        """
        try:
            offset = (page - 1) * page_size

            if session_id:
                records = await self.repository.get_by_user_and_session(
                    session, user_id, session_id, page_size, offset
                )
                total = await self.repository.count_by_user_and_session(
                    session, user_id, session_id
                )
            else:
                records = await self.repository.get_by_user(
                    session, user_id, page_size, offset
                )
                # Simple count for user
                total = len(records)  # Simplified

            items = [
                {
                    "id": record.id,
                    "user_id": record.user_id,
                    "session_id": record.session_id,
                    "file_name": record.file_name,
                    "cv_language": record.cv_language,
                    "status": record.status,
                    "created_at": record.created_at,
                }
                for record in records
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }

        except Exception as e:
            logger.error(f"Failed to get user history: {str(e)}")
            raise ParserError(f"Failed to retrieve history: {str(e)}")

    async def create_placeholder_job(
        self,
        session: AsyncSession,
        job_id: UUID,
        user_id: str,
        session_id: str,
        file_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a placeholder job record for background processing.

        Args:
            session: Database session
            job_id: Pre-generated job UUID
            user_id: User identifier
            session_id: Session identifier
            file_name: Optional filename

        Returns:
            Job information

        Raises:
            ParserError: If creation fails
        """
        try:
            db_record = await self.repository.create(
                session=session,
                record_id=job_id,
                user_id=user_id,
                session_id=session_id,
                parsed_data={},
                file_name=file_name,
                status="processing",
            )

            logger.info(
                f"Created placeholder job: {job_id} for user: {user_id}, "
                f"session: {session_id}"
            )

            return {
                "job_id": db_record.id,
                "status": "processing",
                "message": "Job created and processing in background",
            }

        except Exception as e:
            logger.error(f"Failed to create placeholder job: {str(e)}")
            raise ParserError(f"Failed to create job: {str(e)}")

    async def process_file_background(
        self,
        job_id: UUID,
        user_id: str,
        session_id: str,
        file_content: bytes,
        file_name: str,
        file_content_type: str,
        parse_mode: str = "advanced",
    ):
        """Process CV file in background.

        This method runs in BackgroundTasks and updates the job status.

        Args:
            job_id: Job UUID
            user_id: User identifier
            session_id: Session identifier
            file_content: File content as bytes
            file_name: Original filename
            file_content_type: File MIME type
            parse_mode: Parse mode (basic/advanced)
        """
        start_time = time.time()
        db_manager = get_db_manager()

        try:
            logger.info(
                f"🚀 [BACKGROUND] Starting file parsing for job: {job_id}, "
                f"user: {user_id}, file: {file_name}, mode: {parse_mode}"
            )

            # Save file to storage first
            storage_start = time.time()
            stored_file_path = None
            try:
                stored_file_path = self.storage_manager.save_file(
                    file_content=file_content,
                    original_filename=file_name,
                    job_id=job_id,
                )
                storage_time = time.time() - storage_start
                if stored_file_path:
                    logger.info(
                        f"💾 [BACKGROUND] File saved to storage in {storage_time:.2f}s: {stored_file_path}"
                    )
            except Exception as storage_error:
                logger.warning(
                    f"⚠️ [BACKGROUND] Failed to save file to storage: {str(storage_error)}"
                )
                # Continue processing even if storage fails

            # Extract text from file
            file_start = time.time()
            extraction_result = await self.file_service.extract_text_from_content(
                file_content, file_name
            )
            extracted_text = extraction_result["content"]
            file_time = time.time() - file_start

            logger.info(
                f"📄 [BACKGROUND] File extraction completed in {file_time:.2f}s"
            )

            # Validate extracted text
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise ValidationError("Extracted text is too short to parse")

            # Parse with OpenAI
            openai_start = time.time()
            parsed_result = await self.openai_service.parse_cv(
                extracted_text, parse_mode=parse_mode
            )
            openai_time = time.time() - openai_start

            logger.info(
                f"⏱️ [BACKGROUND] OpenAI parsing completed in {openai_time:.2f}s"
            )

            # Extract metadata
            metadata = parsed_result.pop("_metadata", {})
            cv_language = parsed_result.get("cv_language")
            processing_time = time.time() - start_time

            # Update database with success
            async with db_manager.get_session() as session:
                await self.repository.update_status(
                    session=session, record_id=job_id, status="success"
                )

                # Update with full data
                record = await self.repository.get_by_id(session, job_id)
                if record:
                    record.parsed_data = parsed_result
                    record.input_text = extracted_text[:5000]
                    record.file_mime_type = extraction_result["mime_type"]
                    record.stored_file_path = stored_file_path
                    record.cv_language = cv_language
                    record.processing_time_seconds = processing_time
                    record.openai_model = metadata.get("model")
                    record.tokens_used = metadata.get("tokens_used")

                    await session.flush()

            logger.info(
                f"✅ [BACKGROUND] Successfully completed job: {job_id} | "
                f"Total: {processing_time:.2f}s, File: {file_time:.2f}s, "
                f"OpenAI: {openai_time:.2f}s, Stored: {stored_file_path}"
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ [BACKGROUND] Failed job {job_id}: {str(e)}")

            # Update database with failure
            try:
                async with db_manager.get_session() as session:
                    await self.repository.update_status(
                        session=session,
                        record_id=job_id,
                        status="failed",
                        error_message=str(e),
                    )

                    # Update processing time even on failure
                    record = await self.repository.get_by_id(session, job_id)
                    if record:
                        record.processing_time_seconds = processing_time
                        await session.flush()

            except Exception as db_error:
                logger.error(f"Failed to update error status: {str(db_error)}")

    async def process_text_background(
        self, job_id: UUID, user_id: str, session_id: str, text: str
    ):
        """Process CV text in background.

        Args:
            job_id: Job UUID
            user_id: User identifier
            session_id: Session identifier
            text: CV text content
        """
        start_time = time.time()
        db_manager = get_db_manager()

        try:
            logger.info(
                f"🚀 [BACKGROUND] Starting text parsing for job: {job_id}, "
                f"user: {user_id}, text length: {len(text)}"
            )

            # Validate input
            if not text or len(text.strip()) < 10:
                raise ValidationError("Text is too short to parse")

            # Parse with OpenAI
            openai_start = time.time()
            parsed_result = await self.openai_service.parse_cv(text)
            openai_time = time.time() - openai_start

            logger.info(
                f"⏱️ [BACKGROUND] OpenAI parsing completed in {openai_time:.2f}s"
            )

            # Extract metadata
            metadata = parsed_result.pop("_metadata", {})
            cv_language = parsed_result.get("cv_language")
            processing_time = time.time() - start_time

            # Update database with success
            async with db_manager.get_session() as session:
                await self.repository.update_status(
                    session=session, record_id=job_id, status="success"
                )

                record = await self.repository.get_by_id(session, job_id)
                if record:
                    record.parsed_data = parsed_result
                    record.input_text = text[:5000]
                    record.cv_language = cv_language
                    record.processing_time_seconds = processing_time
                    record.openai_model = metadata.get("model")
                    record.tokens_used = metadata.get("tokens_used")

                    await session.flush()

            logger.info(
                f"✅ [BACKGROUND] Successfully completed job: {job_id} | "
                f"Total: {processing_time:.2f}s, OpenAI: {openai_time:.2f}s"
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ [BACKGROUND] Failed job {job_id}: {str(e)}")

            try:
                async with db_manager.get_session() as session:
                    await self.repository.update_status(
                        session=session,
                        record_id=job_id,
                        status="failed",
                        error_message=str(e),
                    )

                    record = await self.repository.get_by_id(session, job_id)
                    if record:
                        record.processing_time_seconds = processing_time
                        await session.flush()

            except Exception as db_error:
                logger.error(f"Failed to update error status: {str(db_error)}")


def get_parser_service() -> ParserService:
    """Get parser service instance."""
    return ParserService()
