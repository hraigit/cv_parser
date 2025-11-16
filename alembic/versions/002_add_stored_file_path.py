"""Add stored_file_path to parsed_cvs table

Revision ID: 002_add_stored_file_path
Revises: 001_initial_schema
Create Date: 2025-11-16 14:30:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002_add_stored_file_path"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add stored_file_path column to parsed_cvs table."""
    op.add_column(
        "parsed_cvs",
        sa.Column(
            "stored_file_path",
            sa.String(length=1000),
            nullable=True,
            comment="Full path to stored file on disk",
        ),
    )


def downgrade() -> None:
    """Remove stored_file_path column from parsed_cvs table."""
    op.drop_column("parsed_cvs", "stored_file_path")
