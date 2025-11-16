"""Parser API routes."""

from typing import Optional
from uuid import UUID, uuid4

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
    "/result/{job_id}",
    response_model=dict,
    summary="Get parse result by job ID",
    description="Retrieve parsed CV result by job ID (same as record ID)",
)
async def get_result(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get parse result by job ID.

    Args:
        job_id: Job/Record UUID
        db: Database session

    Returns:
        Parsed CV data
    """
    try:
        parser_service = get_parser_service()
        result = await parser_service.get_parse_result(session=db, record_id=job_id)

        if not result:
            raise HTTPException(
                status_code=404, detail=f"Parse result not found: {job_id}"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parse result: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/latest/{user_id}",
    response_model=dict,
    summary="Get latest CV for user",
    description="Retrieve the most recently parsed CV for a user (sorted by created_at DESC)",
)
async def get_latest_cv(
    user_id: str,
    session_id: Optional[str] = Query(None, description="Optional session filter"),
    db: AsyncSession = Depends(get_db),
):
    """Get latest parsed CV for a user.

    Args:
        user_id: User identifier
        session_id: Optional session identifier filter
        db: Database session

    Returns:
        Latest parsed CV data
    """
    try:
        parser_service = get_parser_service()
        result = await parser_service.get_latest_cv(
            session=db, user_id=user_id, session_id=session_id
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No CV found for user: {user_id}"
                + (f", session: {session_id}" if session_id else ""),
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest CV: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/history/{user_id}",
    response_model=dict,
    summary="Get user parse history",
    description="Retrieve parsing history for a user with optional session filter",
)
async def get_history(
    user_id: str,
    session_id: Optional[str] = Query(None, description="Optional session filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
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
            page_size=page_size,
        )
        return result

    except Exception as e:
        logger.error(f"Error getting user history: {str(e)}")
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
        "Async endpoint: Returns job ID immediately and processes file in background. "
        "Use /job/{job_id} to check status and /result/{job_id} to get final result."
    ),
)
async def parse_file_async(
    background_tasks: BackgroundTasks,
    user_id: str = Form(..., description="User identifier"),
    session_id: str = Form(..., description="Session identifier"),
    file: UploadFile = File(..., description="CV file to parse"),
    parse_mode: str = Form("advanced", description="Parse mode: 'basic' or 'advanced'"),
    db: AsyncSession = Depends(get_db),
):
    """Parse CV from file asynchronously.

    Returns job ID immediately and processes in background.
    Check status with GET /job/{job_id}.

    Args:
        background_tasks: FastAPI background tasks
        user_id: User identifier
        session_id: Session identifier
        file: Uploaded CV file
        parse_mode: Parse mode (basic/advanced)
        db: Database session

    Returns:
        Job information with job_id for tracking
    """
    try:
        # Validate parse_mode
        if parse_mode not in ["basic", "advanced"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parse_mode: {parse_mode}. Must be 'basic' or 'advanced'",
            )

        # Generate job ID
        job_id = uuid4()

        # Read file content (need to do this before background task)
        file_content = await file.read()
        file_name = file.filename or "unknown"
        file_content_type = file.content_type or "application/octet-stream"

        parser_service = get_parser_service()

        # Create placeholder job in DB
        await parser_service.create_placeholder_job(
            session=db,
            job_id=job_id,
            user_id=user_id,
            session_id=session_id,
            file_name=file_name,
            _type=file_content_type,
        )

        # Commit the placeholder before starting background task
        await db.commit()

        # Add background task
        background_tasks.add_task(
            parser_service.process_file_background,
            job_id=job_id,
            user_id=user_id,
            session_id=session_id,
            file_content=file_content,
            file_name=file_name,
            file_content_type=file_content_type,
            parse_mode=parse_mode,
        )

        logger.info(
            f"Created async file parsing job: {job_id} for user: {user_id}, "
            f"file: {file_name}, mode: {parse_mode}"
        )

        return AsyncJobResponse(
            job_id=job_id,
            status="processing",
            message=f"Job created successfully. Check status at /api/v1/parser/job/{job_id}",
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
        "Async endpoint: Returns job ID immediately and processes text in background. "
        "Supports both formatted CV text and free-form self-descriptions. "
        "Parse modes: 'basic' for high-level summary, 'advanced' for full detailed parsing (default)."
    ),
)
async def parse_text_async(
    background_tasks: BackgroundTasks,
    user_id: str = Form(..., description="User identifier"),
    session_id: str = Form(..., description="Session identifier"),
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
        user_id: User identifier
        session_id: Session identifier
        text: CV text content
        parse_mode: Parse mode (basic/advanced)
        db: Database session

    Returns:
        Job information with job_id for tracking
    """
    try:
        # Validate parse_mode
        if parse_mode not in ["basic", "advanced"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parse_mode: {parse_mode}. Must be 'basic' or 'advanced'",
            )

        # Generate job ID
        job_id = uuid4()

        parser_service = get_parser_service()

        # Create placeholder job
        await parser_service.create_placeholder_job(
            session=db,
            job_id=job_id,
            user_id=user_id,
            session_id=session_id,
            _type="free_text",
        )

        # Commit before background task
        await db.commit()

        # Add background task
        background_tasks.add_task(
            parser_service.process_text_background,
            job_id=job_id,
            user_id=user_id,
            session_id=session_id,
            text=text,
            parse_mode=parse_mode,
        )

        logger.info(
            f"Created async text parsing job: {job_id} for user: {user_id}, mode: {parse_mode}"
        )

        return AsyncJobResponse(
            job_id=job_id,
            status="processing",
            message=f"Job created successfully. Check status at /api/v1/parser/job/{job_id}",
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in parse_text_async: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/job/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Check the status of an async parsing job. Returns 'processing', 'success', or 'failed'.",
)
async def get_job_status(job_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get status of async parsing job.

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        Job status information
    """
    try:
        parser_service = get_parser_service()
        record = await parser_service.get_parse_result(session=db, record_id=job_id)

        if not record:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        return JobStatusResponse(
            job_id=record["id"],
            status=record["status"],
            user_id=record["user_id"],
            session_id=record["session_id"],
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
