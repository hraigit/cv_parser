"""Parser service - business logic layer."""

import time
from typing import Any, Dict, Literal, Optional
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
                "candidate_id": db_record.candidate_id,
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
            logger.error(f"Failed to retrieve parse result: {str(e)}")
            raise ParserError(f"Failed to retrieve parse result: {str(e)}") from e

    async def create_placeholder_job(
        self,
        session: AsyncSession,
        candidate_id: UUID,
        file_name: Optional[str] = None,
        _type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a placeholder job record for background processing.

        Args:
            session: Database session
            candidate_id: Candidate identifier (used as job ID)
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
                candidate_id=candidate_id,
                record_id=candidate_id,  # Use candidate_id as record ID
                parsed_data={},
                file_name=file_name,
                status="processing",
                _type=_type,
            )

            logger.info(f"Created placeholder job for candidate: {candidate_id}")

            return {
                "candidate_id": db_record.candidate_id,
                "status": "processing",
                "message": "Job created and processing in background",
            }

        except Exception as e:
            logger.error(f"Failed to create placeholder job: {str(e)}")
            raise ParserError(f"Failed to create job: {str(e)}") from e

    async def process_file_background(
        self,
        candidate_id: UUID,
        file_content: bytes,
        file_name: str,
        parse_mode: Literal["basic", "advanced"] = "advanced",
    ):
        """Process CV file in background.

        This method runs in BackgroundTasks and updates the job status.

        Args:
            candidate_id: Candidate identifier (used as job ID)
            file_content: File content as bytes
            file_name: Original filename
            parse_mode: Parse mode (basic/advanced)
        """
        start_time = time.time()
        db_manager = get_db_manager()

        try:
            logger.info(
                f"🚀 [BACKGROUND] Starting file parsing for candidate: {candidate_id}, "
                f"file: {file_name}, mode: {parse_mode}"
            )

            # Save file to storage first
            storage_start = time.time()
            stored_file_path = None
            try:
                stored_file_path = self.storage_manager.save_file(
                    file_content=file_content,
                    original_filename=file_name,
                    job_id=candidate_id,
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
            is_image = extraction_result.get("is_image", False)
            mime_type = extraction_result["mime_type"]
            file_time = time.time() - file_start

            logger.info(
                f"📄 [BACKGROUND] File extraction completed in {file_time:.2f}s "
                f"({'IMAGE format' if is_image else 'TEXT format'})"
            )

            # Parse based on file type
            openai_start = time.time()

            if is_image:
                # Use Vision API for images
                logger.info("🖼️ [BACKGROUND] Using Vision API for image file")
                raw_bytes = extraction_result.get("raw_bytes")
                if not raw_bytes:
                    raise ValidationError("Image bytes not available for Vision API")

                parsed_result = await self.openai_service.parse_cv_from_image(
                    image_content=raw_bytes, mime_type=mime_type, parse_mode=parse_mode
                )
                extracted_text = f"[Image CV - {mime_type}]"  # Placeholder for DB
            else:
                # Use text API for text-based files
                # Validate extracted text
                if not extracted_text or len(extracted_text.strip()) < 10:
                    raise ValidationError("Extracted text is too short to parse")

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
                    session=session, record_id=candidate_id, status="success"
                )

                # Update with full data
                record = await self.repository.get_by_id(session, candidate_id)
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
                f"✅ [BACKGROUND] Successfully completed candidate: {candidate_id} | "
                f"Total: {processing_time:.2f}s, File: {file_time:.2f}s, "
                f"OpenAI: {openai_time:.2f}s, Stored: {stored_file_path}"
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ [BACKGROUND] Failed candidate {candidate_id}: {str(e)}")

            # Update database with failure
            try:
                async with db_manager.get_session() as session:
                    await self.repository.update_status(
                        session=session,
                        record_id=candidate_id,
                        status="failed",
                        error_message=str(e),
                    )

                    # Update processing time even on failure
                    record = await self.repository.get_by_id(session, candidate_id)
                if record:
                    record.processing_time_seconds = processing_time
                    await session.flush()

            except Exception as db_error:
                logger.error(f"Failed to update error status: {str(db_error)}")

    async def process_text_background(
        self,
        candidate_id: UUID,
        text: str,
        parse_mode: Literal["basic", "advanced"] = "advanced",
    ):
        """Process CV text in background.

        Args:
            candidate_id: Candidate identifier (used as job ID)
            text: CV text content
            parse_mode: Parse mode ('basic' or 'advanced')
        """
        start_time = time.time()
        db_manager = get_db_manager()

        try:
            logger.info(
                f"🚀 [BACKGROUND] Starting text parsing for candidate: {candidate_id}, "
                f"text length: {len(text)}, mode: {parse_mode}"
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
                    session=session, record_id=candidate_id, status="success"
                )

                record = await self.repository.get_by_id(session, candidate_id)
                if record:
                    record.parsed_data = parsed_result
                    record.input_text = text[:8000]
                    record.cv_language = cv_language
                    record.processing_time_seconds = processing_time
                    record.openai_model = metadata.get("model")
                    record.tokens_used = metadata.get("tokens_used")

                    await session.flush()

            logger.info(
                f"✅ [BACKGROUND] Successfully completed candidate: {candidate_id} | "
                f"Total: {processing_time:.2f}s, OpenAI: {openai_time:.2f}s"
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ [BACKGROUND] Failed candidate {candidate_id}: {str(e)}")

            try:
                async with db_manager.get_session() as session:
                    await self.repository.update_status(
                        session=session,
                        record_id=candidate_id,
                        status="failed",
                        error_message=str(e),
                    )

                    record = await self.repository.get_by_id(session, candidate_id)
                    if record:
                        record.processing_time_seconds = processing_time
                        await session.flush()

            except Exception as db_error:
                logger.error(f"Failed to update error status: {str(db_error)}")


def get_parser_service() -> ParserService:
    """Get parser service instance."""
    return ParserService()
