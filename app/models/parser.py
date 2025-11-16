"""Database models for parser."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ParsedCV(Base):
    """Model for storing parsed CV data."""

    __tablename__ = "parsed_cvs"

    # Primary key - using candidate_id as both primary key and identifier
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True
    )

    # Candidate identifier (replaces user_id and session_id)
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )

    # Input data
    input_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stored_file_path: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="Full path to stored file on disk"
    )
    _type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Parsed data
    parsed_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Language
    cv_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Processing metadata
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    openai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="success")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Indexes for better query performance
    __table_args__ = (
        Index("idx_candidate_id", "candidate_id"),
        Index("idx_created_at", "created_at"),
        Index("idx_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ParsedCV(id={self.id}, candidate_id={self.candidate_id}, "
            f"status={self.status})>"
        )
