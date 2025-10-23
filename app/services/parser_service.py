"""Parser service - business logic layer."""
import time
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.exceptions.custom_exceptions import (
    ParserError,
    EntityExtractionError,
    ValidationError
)
from app.repositories.parser_repository import get_parser_repository
from app.schemas.parser import ParsedCVData
from app.services.file_service import get_file_service
from app.services.openai_service import get_openai_service


class ParserService:
    """Service for CV/Entity parsing operations."""
    
    def __init__(self):
        """Initialize parser service."""
        self.file_service = get_file_service()
        self.openai_service = get_openai_service()
        self.repository = get_parser_repository()
    
    async def parse_from_text(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        text: str
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
                f"Starting text parsing for user: {user_id}, "
                f"session: {session_id}, text length: {len(text)}"
            )
            
            # Validate input
            if not text or len(text.strip()) < 10:
                raise ValidationError("Text is too short to parse")
            
            # Parse with OpenAI
            parsed_result = await self.openai_service.parse_cv(text)
            
            # Extract metadata
            metadata = parsed_result.pop("_metadata", {})
            
            # Get CV language from parsed data
            cv_language = parsed_result.get("cv_language")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save to database
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
                status="success"
            )
            
            logger.info(
                f"Successfully parsed text for user: {user_id}, "
                f"session: {session_id}, record_id: {db_record.id}"
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
                "created_at": db_record.created_at
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
                    error_message=str(e)
                )
            except Exception as db_error:
                logger.error(f"Failed to save error record: {str(db_error)}")
            
            raise ParserError(f"Failed to parse CV from text: {str(e)}")
    
    async def parse_from_free_text(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        free_text: str
    ) -> Dict[str, Any]:
        """Parse CV from free-form text where candidate describes themselves.
        
        Args:
            session: Database session
            user_id: User identifier
            session_id: Session identifier
            free_text: Free-form text where candidate describes themselves
            
        Returns:
            Parsed CV data with metadata
            
        Raises:
            ParserError: If parsing fails
        """
        start_time = time.time()
        
        try:
            logger.info(
                f"Starting free text parsing for user: {user_id}, "
                f"session: {session_id}, text length: {len(free_text)}"
            )
            
            # Validate input
            if not free_text or len(free_text.strip()) < 20:
                raise ValidationError("Free text is too short to parse (minimum 20 characters)")
            
            # Add context to help OpenAI understand this is a self-description
            contextualized_text = f"""The following is a candidate's self-description. Please extract their CV information from their own words:

{free_text}"""
            
            # Parse with OpenAI
            parsed_result = await self.openai_service.parse_cv(contextualized_text)
            
            # Extract metadata
            metadata = parsed_result.pop("_metadata", {})
            
            # Get CV language from parsed data
            cv_language = parsed_result.get("cv_language")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save to database with original free text
            db_record = await self.repository.create(
                session=session,
                user_id=user_id,
                session_id=session_id,
                parsed_data=parsed_result,
                input_text=free_text[:5000],  # Store first 5000 chars of original text
                cv_language=cv_language,
                processing_time_seconds=processing_time,
                openai_model=metadata.get("model"),
                tokens_used=metadata.get("tokens_used"),
                status="success"
            )
            
            logger.info(
                f"Successfully parsed free text for user: {user_id}, "
                f"session: {session_id}, record_id: {db_record.id}"
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
                "created_at": db_record.created_at
            }
            
        except ValidationError:
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"Failed to parse free text for user: {user_id}, "
                f"session: {session_id}: {str(e)}"
            )
            
            # Save error to database
            try:
                await self.repository.create(
                    session=session,
                    user_id=user_id,
                    session_id=session_id,
                    parsed_data={},
                    input_text=free_text[:5000],
                    processing_time_seconds=processing_time,
                    status="failed",
                    error_message=str(e)
                )
            except Exception as db_error:
                logger.error(f"Failed to save error record: {str(db_error)}")
            
            raise ParserError(f"Failed to parse CV from free text: {str(e)}")
    
    async def parse_from_file(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        file: UploadFile
    ) -> Dict[str, Any]:
        """Parse CV from uploaded file.
        
        Args:
            session: Database session
            user_id: User identifier
            session_id: Session identifier
            file: Uploaded file
            
        Returns:
            Parsed CV data with metadata
            
        Raises:
            ParserError: If parsing fails
        """
        start_time = time.time()
        
        try:
            logger.info(
                f"Starting file parsing for user: {user_id}, "
                f"session: {session_id}, file: {file.filename}"
            )
            
            # Extract text from file
            extraction_result = await self.file_service.extract_text_from_file(file)
            extracted_text = extraction_result["content"]
            
            # Validate extracted text
            if not extracted_text or len(extracted_text.strip()) < 10:
                raise ValidationError("Extracted text is too short to parse")
            
            # Parse with OpenAI
            parsed_result = await self.openai_service.parse_cv(extracted_text)
            
            # Extract metadata
            metadata = parsed_result.pop("_metadata", {})
            
            # Get CV language
            cv_language = parsed_result.get("cv_language")
            
            # Calculate total processing time
            processing_time = time.time() - start_time
            
            # Save to database
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
                status="success"
            )
            
            logger.info(
                f"Successfully parsed file for user: {user_id}, "
                f"session: {session_id}, record_id: {db_record.id}"
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
                "status": "success",
                "created_at": db_record.created_at
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
                    error_message=str(e)
                )
            except Exception as db_error:
                logger.error(f"Failed to save error record: {str(db_error)}")
            
            raise ParserError(f"Failed to parse CV from file: {str(e)}")
    
    async def get_parse_result(
        self,
        session: AsyncSession,
        record_id: UUID
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
                "updated_at": db_record.updated_at
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
        page_size: int = 10
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
                    "created_at": record.created_at
                }
                for record in records
            ]
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"Failed to get user history: {str(e)}")
            raise ParserError(f"Failed to retrieve history: {str(e)}")


def get_parser_service() -> ParserService:
    """Get parser service instance."""
    return ParserService()