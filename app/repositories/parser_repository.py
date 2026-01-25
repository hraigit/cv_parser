"""Repository for parser database operations."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.exceptions.custom_exceptions import DatabaseError, RecordNotFoundError
from app.models.parser import ParsedCV


class ParserRepository:
    """Repository for parsed CV database operations."""

    async def create(
        self,
        session: AsyncSession,
        candidate_id: str,
        parsed_data: dict,
        input_text: Optional[str] = None,
        file_name: Optional[str] = None,
        file_mime_type: Optional[str] = None,
        stored_file_path: Optional[str] = None,
        cv_language: Optional[str] = None,
        processing_time_seconds: Optional[float] = None,
        openai_model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        record_id: Optional[str] = None,
        _type: Optional[str] = None,
    ) -> ParsedCV:
        """Create or update a parsed CV record (upsert).

        If a record with the same ID already exists, it will be updated.

        Args:
            session: Database session
            candidate_id: Candidate identifier (used as both record ID and identifier)
            parsed_data: Parsed CV data as dictionary
            input_text: Original input text
            file_name: Original filename
            file_mime_type: File MIME type
            stored_file_path: Full path to stored file on disk
            cv_language: Detected CV language
            processing_time_seconds: Processing time
            openai_model: OpenAI model used
            tokens_used: Tokens consumed
            status: Processing status
            error_message: Error message if failed
            record_id: Optional pre-generated UUID for the record
            _type: Type of input (e.g., 'pdf', 'free_text')

        Returns:
            Created or updated ParsedCV instance

        Raises:
            DatabaseError: If operation fails
        """
        try:
            target_id = record_id or candidate_id

            # Check if record already exists by ID first, then by candidate_id
            existing = await self.get_by_id(session, target_id)
            if not existing:
                # Also check by candidate_id to handle updates for existing candidates
                existing = await self.get_by_candidate_id(session, candidate_id)

            if existing:
                # Update existing record
                existing.candidate_id = candidate_id
                existing.parsed_data = parsed_data
                existing.input_text = input_text
                existing.file_name = file_name
                existing.file_mime_type = file_mime_type
                existing.stored_file_path = stored_file_path
                existing.cv_language = cv_language
                existing.processing_time_seconds = processing_time_seconds
                existing.openai_model = openai_model
                existing.tokens_used = tokens_used
                existing.status = status
                existing.error_message = error_message
                existing._type = _type

                await session.flush()
                await session.refresh(existing)

                logger.info(
                    f"Updated existing parsed CV record: {existing.id} "
                    f"for candidate: {candidate_id}"
                )

                return existing

            # Create new record
            parsed_cv = ParsedCV(
                id=target_id,
                candidate_id=candidate_id,
                parsed_data=parsed_data,
                input_text=input_text,
                file_name=file_name,
                file_mime_type=file_mime_type,
                stored_file_path=stored_file_path,
                cv_language=cv_language,
                processing_time_seconds=processing_time_seconds,
                openai_model=openai_model,
                tokens_used=tokens_used,
                status=status,
                error_message=error_message,
                _type=_type,
            )

            session.add(parsed_cv)
            await session.flush()
            await session.refresh(parsed_cv)

            logger.info(
                f"Created parsed CV record: {parsed_cv.id} "
                f"for candidate: {candidate_id}"
            )

            return parsed_cv

        except Exception as e:
            logger.error(f"Failed to create/update parsed CV record: {str(e)}")
            raise DatabaseError(f"Failed to create parsed CV: {str(e)}") from e

    async def get_by_id(
        self, session: AsyncSession, record_id: str
    ) -> Optional[ParsedCV]:
        """Get parsed CV by ID.

        Args:
            session: Database session
            record_id: Record UUID

        Returns:
            ParsedCV instance or None

        Raises:
            DatabaseError: If query fails
        """
        try:
            stmt = select(ParsedCV).where(ParsedCV.id == record_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get parsed CV by ID {record_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve parsed CV: {str(e)}") from e

    async def get_by_candidate_id(
        self, session: AsyncSession, candidate_id: str
    ) -> Optional[ParsedCV]:
        """Get parsed CV by candidate ID.

        Args:
            session: Database session
            candidate_id: Candidate UUID

        Returns:
            ParsedCV instance or None

        Raises:
            DatabaseError: If query fails
        """
        try:
            stmt = select(ParsedCV).where(ParsedCV.candidate_id == candidate_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Failed to get parsed CV by candidate_id {candidate_id}: {str(e)}"
            )
            raise DatabaseError(f"Failed to retrieve parsed CV: {str(e)}") from e

    async def update_status(
        self,
        session: AsyncSession,
        record_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> ParsedCV:
        """Update status of parsed CV record.

        Args:
            session: Database session
            record_id: Record UUID
            status: New status
            error_message: Error message if failed

        Returns:
            Updated ParsedCV instance

        Raises:
            RecordNotFoundError: If record not found
            DatabaseError: If update fails
        """
        try:
            parsed_cv = await self.get_by_id(session, record_id)

            if not parsed_cv:
                raise RecordNotFoundError(f"Parsed CV not found: {record_id}")

            parsed_cv.status = status
            parsed_cv.error_message = error_message

            await session.flush()
            await session.refresh(parsed_cv)

            logger.info(f"Updated status for parsed CV {record_id}: {status}")

            return parsed_cv

        except RecordNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update parsed CV status: {str(e)}")
            raise DatabaseError(f"Failed to update parsed CV: {str(e)}") from e

    async def delete(self, session: AsyncSession, record_id: str) -> bool:
        """Delete parsed CV record.

        Args:
            session: Database session
            record_id: Record UUID

        Returns:
            True if deleted, False if not found

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            parsed_cv = await self.get_by_id(session, record_id)

            if not parsed_cv:
                return False

            await session.delete(parsed_cv)
            await session.flush()

            logger.info(f"Deleted parsed CV: {record_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete parsed CV {record_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete parsed CV: {str(e)}") from e


def get_parser_repository() -> ParserRepository:
    """Get parser repository instance."""
    return ParserRepository()
