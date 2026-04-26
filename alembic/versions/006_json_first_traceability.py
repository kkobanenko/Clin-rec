"""json first traceability

Revision ID: 006
Revises: 005
Create Date: 2026-04-26

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("document_section", sa.Column("source_artifact_id", sa.Integer(), nullable=True))
    op.add_column("document_section", sa.Column("source_artifact_type", sa.String(length=32), nullable=True))
    op.add_column("document_section", sa.Column("source_block_id", sa.String(length=128), nullable=True))
    op.add_column("document_section", sa.Column("source_path", sa.Text(), nullable=True))
    op.create_index("ix_document_section_source_block_id", "document_section", ["source_block_id"], unique=False)
    op.create_foreign_key(
        "fk_document_section_source_artifact",
        "document_section",
        "source_artifact",
        ["source_artifact_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("text_fragment", sa.Column("source_artifact_id", sa.Integer(), nullable=True))
    op.add_column("text_fragment", sa.Column("source_artifact_type", sa.String(length=32), nullable=True))
    op.add_column("text_fragment", sa.Column("source_block_id", sa.String(length=128), nullable=True))
    op.add_column("text_fragment", sa.Column("source_path", sa.Text(), nullable=True))
    op.add_column("text_fragment", sa.Column("content_kind", sa.String(length=32), nullable=True))
    op.add_column("text_fragment", sa.Column("extraction_confidence", sa.Float(), nullable=True))
    op.create_index("ix_text_fragment_source_block_id", "text_fragment", ["source_block_id"], unique=False)
    op.create_index("ix_text_fragment_source_artifact_id", "text_fragment", ["source_artifact_id"], unique=False)
    op.create_foreign_key(
        "fk_text_fragment_source_artifact",
        "text_fragment",
        "source_artifact",
        ["source_artifact_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_text_fragment_source_artifact", "text_fragment", type_="foreignkey")
    op.drop_index("ix_text_fragment_source_artifact_id", table_name="text_fragment")
    op.drop_index("ix_text_fragment_source_block_id", table_name="text_fragment")
    op.drop_column("text_fragment", "extraction_confidence")
    op.drop_column("text_fragment", "content_kind")
    op.drop_column("text_fragment", "source_path")
    op.drop_column("text_fragment", "source_block_id")
    op.drop_column("text_fragment", "source_artifact_type")
    op.drop_column("text_fragment", "source_artifact_id")

    op.drop_constraint("fk_document_section_source_artifact", "document_section", type_="foreignkey")
    op.drop_index("ix_document_section_source_block_id", table_name="document_section")
    op.drop_column("document_section", "source_path")
    op.drop_column("document_section", "source_block_id")
    op.drop_column("document_section", "source_artifact_type")
    op.drop_column("document_section", "source_artifact_id")