"""Parser service - business logic layer."""

import time
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_manager
from app.core.logging import logger
from app.exceptions.custom_exceptions import ParserError, ValidationError
from app.repositories.parser_repository import get_parser_repository
from app.services.file_service import get_file_service
from app.services.openai_service import get_openai_service
from app.utils.experience_utils import (
    calculate_total_experience_years,
    enrich_educations,
    enrich_professional_experiences,
)
from app.utils.storage_utils import get_file_storage_manager


class ParserService:
    """Service for CV/Entity parsing operations."""

    def __init__(self):
        """Initialize parser service."""
        self.file_service = get_file_service()
        self.openai_service = get_openai_service()
        self.repository = get_parser_repository()
        self.storage_manager = get_file_storage_manager()

    def _enrich_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich parsed data with calculated fields.

        Args:
            parsed_data: Raw parsed data from OpenAI

        Returns:
            Enriched data with calculated experience and durations
        """
        try:
            # Get professional experiences
            profile = parsed_data.get("profile", {})
            experiences = profile.get("professional_experiences", [])

            # Enrich each experience with duration_in_months
            if experiences:
                enriched_experiences = enrich_professional_experiences(experiences)
                profile["professional_experiences"] = enriched_experiences

                # Calculate and add total experience to basics
                total_exp_years = calculate_total_experience_years(experiences)
                if "basics" not in profile:
                    profile["basics"] = {}
                profile["basics"]["total_experience_in_years"] = total_exp_years

            # Enrich educations with duration_in_years
            educations = profile.get("educations", [])
            if educations:
                enriched_educations = enrich_educations(educations)
                profile["educations"] = enriched_educations

            parsed_data["profile"] = profile

        except Exception as e:
            logger.warning(f"Failed to enrich parsed data: {str(e)}")

        return parsed_data

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
                "stored_file_path": db_record.stored_file_path,
                "processing_time_seconds": db_record.processing_time_seconds,
                "status": db_record.status,
                "error_message": db_record.error_message,
                "created_at": db_record.created_at,
                "updated_at": db_record.updated_at,
            }

        except Exception as e:
            logger.error(f"Failed to get parse result {record_id}: {str(e)}")
            raise ParserError(f"Failed to retrieve parse result: {str(e)}")

    async def get_latest_cv(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the most recently parsed CV for a user.

        Args:
            session: Database session
            user_id: User identifier
            session_id: Optional session filter

        Returns:
            Latest CV data or None
        """
        try:
            from sqlalchemy import desc, select

            from app.models.parser import ParsedCV

            # Build query
            query = select(ParsedCV).where(ParsedCV.user_id == user_id)

            # Add session filter if provided
            if session_id:
                query = query.where(ParsedCV.session_id == session_id)

            # Order by created_at DESC and get first result
            query = query.order_by(desc(ParsedCV.created_at)).limit(1)

            result = await session.execute(query)
            db_record = result.scalar_one_or_none()

            if not db_record:
                return None

            return {
                "id": db_record.id,
                "user_id": db_record.user_id,
                "session_id": db_record.session_id,
                "parsed_data": db_record.parsed_data,
                "cv_language": db_record.cv_language,
                "file_name": db_record.file_name,
                "stored_file_path": db_record.stored_file_path,
                "processing_time_seconds": db_record.processing_time_seconds,
                "status": db_record.status,
                "error_message": db_record.error_message,
                "created_at": db_record.created_at,
                "updated_at": db_record.updated_at,
            }

        except Exception as e:
            logger.error(f"Failed to get latest CV for user {user_id}: {str(e)}")
            raise ParserError(f"Failed to retrieve latest CV: {str(e)}")

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
        _type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a placeholder job record for background processing.

        Args:
            session: Database session
            job_id: Pre-generated job UUID
            user_id: User identifier
            session_id: Session identifier
            file_name: Optional filename
            _type: Type of input (e.g., 'pdf', 'free_text')

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
                _type=_type,
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

            # Enrich parsed data with calculated fields
            parsed_result = self._enrich_parsed_data(parsed_result)

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
                    record.input_text = extracted_text[:8000]
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
        self,
        job_id: UUID,
        user_id: str,
        session_id: str,
        text: str,
        parse_mode: str = "advanced",
    ):
        """Process CV text in background.

        Args:
            job_id: Job UUID
            user_id: User identifier
            session_id: Session identifier
            text: CV text content
            parse_mode: Parse mode ('basic' or 'advanced')
        """
        start_time = time.time()
        db_manager = get_db_manager()

        try:
            logger.info(
                f"🚀 [BACKGROUND] Starting text parsing for job: {job_id}, "
                f"user: {user_id}, text length: {len(text)}, mode: {parse_mode}"
            )

            # Validate input
            if not text or len(text.strip()) < 10:
                raise ValidationError("Text is too short to parse")

            # Parse with OpenAI
            openai_start = time.time()
            parsed_result = await self.openai_service.parse_cv(
                text, parse_mode=parse_mode
            )
            openai_time = time.time() - openai_start

            logger.info(
                f"⏱️ [BACKGROUND] OpenAI parsing completed in {openai_time:.2f}s"
            )

            # Extract metadata
            metadata = parsed_result.pop("_metadata", {})

            # Enrich parsed data with calculated fields
            parsed_result = self._enrich_parsed_data(parsed_result)

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
                    record.input_text = text[:8000]
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
