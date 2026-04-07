"""pipeline_event_log for refetch/normalize UI logging

Revision ID: 004
Revises: 003
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pipeline_event_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("document_registry_id", sa.Integer(), nullable=False),
        sa.Column("document_version_id", sa.Integer(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=64), nullable=True),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail_json", JSONB(), nullable=True),
        sa.ForeignKeyConstraint(["document_registry_id"], ["document_registry.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_version.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pipeline_event_log_created_at", "pipeline_event_log", ["created_at"])
    op.create_index("ix_pipeline_event_log_document_registry_id", "pipeline_event_log", ["document_registry_id"])
    op.create_index("ix_pipeline_event_log_document_version_id", "pipeline_event_log", ["document_version_id"])
    op.create_index("ix_pipeline_event_log_celery_task_id", "pipeline_event_log", ["celery_task_id"])


def downgrade() -> None:
    op.drop_table("pipeline_event_log")
