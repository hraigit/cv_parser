"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    # Create parsed_cvs table
    op.create_table(
        'parsed_cvs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('input_text', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(length=500), nullable=True),
        sa.Column('file_mime_type', sa.String(length=100), nullable=True),
        sa.Column('parsed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('cv_language', sa.String(length=10), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('openai_model', sa.String(length=100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_created_at', 'parsed_cvs', ['created_at'], unique=False)
    op.create_index('idx_status', 'parsed_cvs', ['status'], unique=False)
    op.create_index('idx_user_session', 'parsed_cvs', ['user_id', 'session_id'], unique=False)
    op.create_index(op.f('ix_parsed_cvs_id'), 'parsed_cvs', ['id'], unique=False)
    op.create_index(op.f('ix_parsed_cvs_session_id'), 'parsed_cvs', ['session_id'], unique=False)
    op.create_index(op.f('ix_parsed_cvs_user_id'), 'parsed_cvs', ['user_id'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_parsed_cvs_user_id'), table_name='parsed_cvs')
    op.drop_index(op.f('ix_parsed_cvs_session_id'), table_name='parsed_cvs')
    op.drop_index(op.f('ix_parsed_cvs_id'), table_name='parsed_cvs')
    op.drop_index('idx_user_session', table_name='parsed_cvs')
    op.drop_index('idx_status', table_name='parsed_cvs')
    op.drop_index('idx_created_at', table_name='parsed_cvs')
    op.drop_table('parsed_cvs')