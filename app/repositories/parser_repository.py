"""Repository for parser database operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.exceptions.custom_exceptions import DatabaseError, RecordNotFoundError
from app.models.parser import ParsedCV


class ParserRepository:
    """Repository for parsed CV database operations."""

    async def create(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
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
        record_id: Optional[UUID] = None,
        _type: Optional[str] = None,
    ) -> ParsedCV:
        """Create a new parsed CV record.

        Args:
            session: Database session
            user_id: User identifier
            session_id: Session identifier
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
            Created ParsedCV instance

        Raises:
            DatabaseError: If creation fails
        """
        try:
            parsed_cv = ParsedCV(
                id=record_id,  # Will use auto-generated if None
                user_id=user_id,
                session_id=session_id,
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
                f"for user: {user_id}, session: {session_id}"
            )

            return parsed_cv

        except Exception as e:
            logger.error(f"Failed to create parsed CV record: {str(e)}")
            raise DatabaseError(f"Failed to create parsed CV: {str(e)}") from e

    async def get_by_id(
        self, session: AsyncSession, record_id: UUID
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

    async def get_by_user_and_session(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[ParsedCV]:
        """Get parsed CVs by user and session.

        Args:
            session: Database session
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum results
            offset: Results offset

        Returns:
            List of ParsedCV instances

        Raises:
            DatabaseError: If query fails
        """
        try:
            stmt = (
                select(ParsedCV)
                .where(
                    and_(ParsedCV.user_id == user_id, ParsedCV.session_id == session_id)
                )
                .order_by(ParsedCV.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(
                f"Failed to get parsed CVs for user {user_id}, "
                f"session {session_id}: {str(e)}"
            )
            raise DatabaseError(f"Failed to retrieve parsed CVs: {str(e)}") from e

    async def get_by_user(
        self, session: AsyncSession, user_id: str, limit: int = 10, offset: int = 0
    ) -> List[ParsedCV]:
        """Get all parsed CVs for a user.

        Args:
            session: Database session
            user_id: User identifier
            limit: Maximum results
            offset: Results offset

        Returns:
            List of ParsedCV instances
        """
        try:
            stmt = (
                select(ParsedCV)
                .where(ParsedCV.user_id == user_id)
                .order_by(ParsedCV.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get parsed CVs for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve parsed CVs: {str(e)}") from e

    async def count_by_user_and_session(
        self, session: AsyncSession, user_id: str, session_id: str
    ) -> int:
        """Count parsed CVs by user and session.

        Args:
            session: Database session
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Count of records
        """
        try:
            stmt = (
                select(func.count())
                .select_from(ParsedCV)
                .where(
                    and_(ParsedCV.user_id == user_id, ParsedCV.session_id == session_id)
                )
            )

            result = await session.execute(stmt)
            return result.scalar_one()

        except Exception as e:
            logger.error(f"Failed to count parsed CVs: {str(e)}")
            raise DatabaseError(f"Failed to count parsed CVs: {str(e)}") from e

    async def update_status(
        self,
        session: AsyncSession,
        record_id: UUID,
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

    async def delete(self, session: AsyncSession, record_id: UUID) -> bool:
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
