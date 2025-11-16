"""Parser API routes."""

from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import logger
from app.exceptions.custom_exceptions import ValidationError
from app.schemas.parser import AsyncJobResponse, JobStatusResponse
from app.services.parser_service import get_parser_service

router = APIRouter(prefix="/parser", tags=["Parser"])


@router.get(
    "/result/{candidate_id}",
    response_model=dict,
    summary="Get parse result by candidate ID",
    description="Retrieve parsed CV result by candidate ID",
)
async def get_result(candidate_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get parse result by candidate ID.

    Args:
        candidate_id: Candidate UUID
        db: Database session

    Returns:
        Parsed CV data
    """
    try:
        parser_service = get_parser_service()
        result = await parser_service.get_parse_result(
            session=db, record_id=candidate_id
        )

        if not result:
            raise HTTPException(
                status_code=404, detail=f"Parse result not found: {candidate_id}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parse result: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/supported-formats",
    response_model=dict,
    summary="Get supported formats",
    description="Get comprehensive list of supported file formats and MIME types for CV parsing. Includes PDF, Word, HTML, TXT, RTF, CSV, and XML formats.",
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
        "application/vnd.ms-word.document.macroEnabled.12": "Word documents with macros",
    }

    # Group formats by category
    categorized_formats = {
        "pdf": [f for f in formats if "pdf" in f],
        "word": [f for f in formats if any(x in f for x in ["msword", "word", "doc"])],
        "text": [f for f in formats if f.startswith("text/")],
        "html": [f for f in formats if "html" in f or "xml" in f],
        "other": [
            f
            for f in formats
            if not any(x in f for x in ["pdf", "word", "doc", "text/", "html", "xml"])
        ],
    }

    return {
        "supported_formats": formats,
        "count": len(formats),
        "format_descriptions": {
            fmt: format_descriptions.get(fmt, fmt) for fmt in formats
        },
        "categorized_formats": categorized_formats,
        "common_extensions": [
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".html",
            ".htm",
            ".rtf",
            ".csv",
            ".xml",
        ],
    }


@router.get(
    "/cache-stats",
    response_model=dict,
    summary="Get cache statistics",
    description="Get file processing cache statistics",
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


# ============================================================================
# ASYNC BACKGROUND PROCESSING ENDPOINTS
# ============================================================================


@router.post(
    "/parse-file-async",
    response_model=AsyncJobResponse,
    summary="Parse CV from file (Async - Background Processing)",
    description=(
        "Async endpoint: Returns candidate ID immediately and processes file in background. "
        "Use /status/{candidate_id} to check status and /result/{candidate_id} to get final result."
    ),
)
async def parse_file_async(
    background_tasks: BackgroundTasks,
    candidate_id: UUID = Form(..., description="Candidate identifier (used as job ID)"),
    file: UploadFile = File(..., description="CV file to parse"),
    parse_mode: str = Form("advanced", description="Parse mode: 'basic' or 'advanced'"),
    db: AsyncSession = Depends(get_db),
):
    """Parse CV from file asynchronously.

    Returns candidate ID immediately and processes in background.
    Check status with GET /status/{candidate_id}.

    Args:
        background_tasks: FastAPI background tasks
        candidate_id: Candidate identifier (used as job ID)
        file: Uploaded CV file
        parse_mode: Parse mode (basic/advanced)
        db: Database session

    Returns:
        Job information with candidate_id for tracking
    """
    try:
        # Validate parse_mode
        if parse_mode not in ["basic", "advanced"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parse_mode: {parse_mode}. Must be 'basic' or 'advanced'",
            )

        # Read file content (need to do this before background task)
        file_content = await file.read()
        file_name = file.filename or "unknown"
        file_content_type = file.content_type or "application/octet-stream"

        parser_service = get_parser_service()

        # Create placeholder job in DB
        await parser_service.create_placeholder_job(
            session=db,
            candidate_id=candidate_id,
            file_name=file_name,
            _type=file_content_type,
        )

        # Commit the placeholder before starting background task
        await db.commit()

        # Add background task
        background_tasks.add_task(
            parser_service.process_file_background,
            candidate_id=candidate_id,
            file_content=file_content,
            file_name=file_name,
            file_content_type=file_content_type,
            parse_mode=parse_mode,
        )

        logger.info(
            f"Created async file parsing job for candidate: {candidate_id}, "
            f"file: {file_name}, mode: {parse_mode}"
        )

        return AsyncJobResponse(
            candidate_id=candidate_id,
            status="processing",
            message=f"Job created successfully. Check status at /api/v1/parser/status/{candidate_id}",
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Unexpected error in parse_file_async: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post(
    "/parse-text-async",
    response_model=AsyncJobResponse,
    summary="Parse CV from text (Async - Background Processing)",
    description=(
        "Async endpoint: Returns candidate ID immediately and processes text in background. "
        "Supports both formatted CV text and free-form self-descriptions. "
        "Parse modes: 'basic' for high-level summary, 'advanced' for full detailed parsing (default)."
    ),
)
async def parse_text_async(
    background_tasks: BackgroundTasks,
    candidate_id: UUID = Form(..., description="Candidate identifier (used as job ID)"),
    text: str = Form(..., description="CV text content (formatted or free-form)"),
    parse_mode: str = Form("advanced", description="Parse mode: 'basic' or 'advanced'"),
    db: AsyncSession = Depends(get_db),
):
    """Parse CV from text asynchronously.

    Supports both:
    - Formatted CV text (structured resume)
    - Free-form self-descriptions (candidate writes about themselves)

    Args:
        background_tasks: FastAPI background tasks
        candidate_id: Candidate identifier (used as job ID)
        text: CV text content
        parse_mode: Parse mode (basic/advanced)
        db: Database session

    Returns:
        Job information with candidate_id for tracking
    """
    try:
        # Validate parse_mode
        if parse_mode not in ["basic", "advanced"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parse_mode: {parse_mode}. Must be 'basic' or 'advanced'",
            )

        parser_service = get_parser_service()

        # Create placeholder job
        await parser_service.create_placeholder_job(
            session=db,
            candidate_id=candidate_id,
            _type="free_text",
        )

        # Commit before background task
        await db.commit()

        # Add background task
        background_tasks.add_task(
            parser_service.process_text_background,
            candidate_id=candidate_id,
            text=text,
            parse_mode=parse_mode,
        )

        logger.info(
            f"Created async text parsing job for candidate: {candidate_id}, mode: {parse_mode}"
        )

        return AsyncJobResponse(
            candidate_id=candidate_id,
            status="processing",
            message=f"Job created successfully. Check status at /api/v1/parser/status/{candidate_id}",
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in parse_text_async: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/status/{candidate_id}",
    response_model=JobStatusResponse,
    summary="Get job status by candidate ID",
    description="Check the status of an async parsing job. Returns 'processing', 'success', or 'failed'.",
)
async def get_job_status(candidate_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get status of async parsing job.

    Args:
        candidate_id: Candidate UUID
        db: Database session

    Returns:
        Job status information
    """
    try:
        parser_service = get_parser_service()
        record = await parser_service.get_parse_result(
            session=db, record_id=candidate_id
        )

        if not record:
            raise HTTPException(
                status_code=404, detail=f"Job not found: {candidate_id}"
            )

        return JobStatusResponse(
            candidate_id=record["candidate_id"],
            status=record["status"],
            file_name=record.get("file_name"),
            cv_language=record.get("cv_language"),
            processing_time_seconds=record.get("processing_time_seconds"),
            error_message=record.get("error_message"),
            created_at=record["created_at"],
            updated_at=record.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
