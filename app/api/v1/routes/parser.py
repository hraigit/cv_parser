"""Parser API routes."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.exceptions.custom_exceptions import (
    ParserError,
    ValidationError,
    RecordNotFoundError
)
from app.schemas.common import BaseResponse
from app.schemas.parser import (
    ParseTextRequest,
    ParseResponse,
    ParseStatusResponse
)
from app.services.parser_service import get_parser_service

router = APIRouter(prefix="/parser", tags=["Parser"])


@router.post(
    "/parse-text",
    response_model=dict,
    summary="Parse CV from text",
    description="Parse CV/resume from plain text input"
)
async def parse_text(
    request: ParseTextRequest,
    db: AsyncSession = Depends(get_db)
):
    """Parse CV from text input.
    
    Args:
        request: Parse text request with user_id, session_id, and text
        db: Database session
        
    Returns:
        Parsed CV data
    """
    try:
        parser_service = get_parser_service()
        result = await parser_service.parse_from_text(
            session=db,
            user_id=request.user_id,
            session_id=request.session_id,
            text=request.text
        )
        return result
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ParserError as e:
        logger.error(f"Parser error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in parse_text: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/parse-file",
    response_model=dict,
    summary="Parse CV from file",
    description="Parse CV/resume from uploaded file. Supported formats: PDF (.pdf), Word documents (.doc, .docx), HTML (.html, .htm), plain text (.txt), RTF (.rtf), CSV (.csv), XML (.xml)"
)
async def parse_file(
    user_id: str = Form(..., description="User identifier"),
    session_id: str = Form(..., description="Session identifier"),
    file: UploadFile = File(..., description="CV file to parse"),
    db: AsyncSession = Depends(get_db)
):
    """Parse CV from uploaded file.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        file: Uploaded CV file
        db: Database session
        
    Returns:
        Parsed CV data
    """
    try:
        parser_service = get_parser_service()
        result = await parser_service.parse_from_file(
            session=db,
            user_id=user_id,
            session_id=session_id,
            file=file
        )
        return result
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ParserError as e:
        logger.error(f"Parser error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in parse_file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/result/{record_id}",
    response_model=dict,
    summary="Get parse result",
    description="Retrieve parsed CV result by ID"
)
async def get_result(
    record_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get parse result by ID.
    
    Args:
        record_id: Parse result UUID
        db: Database session
        
    Returns:
        Parsed CV data
    """
    try:
        parser_service = get_parser_service()
        result = await parser_service.get_parse_result(
            session=db,
            record_id=record_id
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Parse result not found: {record_id}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parse result: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/history/{user_id}",
    response_model=dict,
    summary="Get user parse history",
    description="Retrieve parsing history for a user with optional session filter"
)
async def get_history(
    user_id: str,
    session_id: Optional[str] = Query(None, description="Optional session filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """Get user parsing history.
    
    Args:
        user_id: User identifier
        session_id: Optional session identifier filter
        page: Page number
        page_size: Items per page
        db: Database session
        
    Returns:
        Paginated history
    """
    try:
        parser_service = get_parser_service()
        result = await parser_service.get_user_history(
            session=db,
            user_id=user_id,
            session_id=session_id,
            page=page,
            page_size=page_size
        )
        return result
        
    except Exception as e:
        logger.error(f"Error getting user history: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/supported-formats",
    response_model=dict,
    summary="Get supported formats",
    description="Get comprehensive list of supported file formats and MIME types for CV parsing. Includes PDF, Word, HTML, TXT, RTF, CSV, and XML formats."
)
async def get_supported_formats():
    """Get supported file formats.
    
    Returns:
        Comprehensive list of supported MIME types with descriptions
    """
    from app.services.file_service import get_file_service
    
    file_service = get_file_service()
    formats = file_service.get_supported_formats()
    
    # Create a mapping of MIME types to human-readable descriptions
    format_descriptions = {
        "application/pdf": "PDF documents (.pdf)",
        "text/plain": "Plain text files (.txt)",
        "text/html": "HTML files (.html, .htm)",
        "application/xhtml+xml": "XHTML files (.xhtml)",
        "application/msword": "Legacy Word documents (.doc)",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Modern Word documents (.docx)",
        "text/rtf": "Rich Text Format (.rtf)",
        "application/rtf": "Rich Text Format (.rtf)",
        "text/csv": "Comma-separated values (.csv)",
        "application/csv": "Comma-separated values (.csv)",
        "text/tab-separated-values": "Tab-separated values (.tsv)",
        "application/xml": "XML files (.xml)",
        "text/xml": "XML files (.xml)",
        "application/octet-stream": "Binary files (fallback for .txt)",
        "text/plain; charset=utf-8": "UTF-8 encoded text",
        "text/plain; charset=ascii": "ASCII encoded text",
        "text/html; charset=utf-8": "UTF-8 encoded HTML",
        "application/doc": "Document files (.doc)",
        "application/vnd.ms-word": "Microsoft Word files",
        "application/vnd.ms-word.document.macroEnabled.12": "Word documents with macros"
    }
    
    # Group formats by category
    categorized_formats = {
        "pdf": [f for f in formats if "pdf" in f],
        "word": [f for f in formats if any(x in f for x in ["msword", "word", "doc"])],
        "text": [f for f in formats if f.startswith("text/")],
        "html": [f for f in formats if "html" in f or "xml" in f],
        "other": [f for f in formats if not any(x in f for x in ["pdf", "word", "doc", "text/", "html", "xml"])]
    }
    
    return {
        "supported_formats": formats,
        "count": len(formats),
        "format_descriptions": {fmt: format_descriptions.get(fmt, fmt) for fmt in formats},
        "categorized_formats": categorized_formats,
        "common_extensions": [".pdf", ".doc", ".docx", ".txt", ".html", ".htm", ".rtf", ".csv", ".xml"]
    }


@router.get(
    "/cache-stats",
    response_model=dict,
    summary="Get cache statistics",
    description="Get file processing cache statistics"
)
async def get_cache_stats():
    """Get cache statistics.
    
    Returns:
        Cache statistics
    """
    from app.services.file_service import get_file_service
    
    file_service = get_file_service()
    stats = file_service.get_cache_stats()
    
    return stats