"""FTS: tsvector on knowledge_artifact (TZ §19 rebuild_indexes).

Revision ID: 003
Revises: 002
Create Date: 2026-04-03

"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE knowledge_artifact ADD COLUMN IF NOT EXISTS search_vector tsvector"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_artifact_search_vector "
        "ON knowledge_artifact USING GIN (search_vector)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_artifact_search_vector")
    op.execute("ALTER TABLE knowledge_artifact DROP COLUMN IF EXISTS search_vector")
