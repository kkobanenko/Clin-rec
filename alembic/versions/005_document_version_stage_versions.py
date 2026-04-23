"""document version stage versions

Revision ID: 005
Revises: 004
Create Date: 2026-04-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("document_version", sa.Column("normalizer_version", sa.String(length=64), nullable=True))
    op.add_column("document_version", sa.Column("compiler_version", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("document_version", "compiler_version")
    op.drop_column("document_version", "normalizer_version")