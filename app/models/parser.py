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

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

    # User and session info
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

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
        Index("idx_user_session", "user_id", "session_id"),
        Index("idx_created_at", "created_at"),
        Index("idx_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ParsedCV(id={self.id}, user_id={self.user_id}, "
            f"session_id={self.session_id}, status={self.status})>"
        )
