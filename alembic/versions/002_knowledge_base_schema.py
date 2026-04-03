"""knowledge base schema

Revision ID: 002
Revises: 001
Create Date: 2026-04-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_artifact",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("canonical_slug", sa.String(512), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("content_md", sa.Text),
        sa.Column("summary", sa.Text),
        sa.Column("confidence", sa.String(32)),
        sa.Column("review_status", sa.String(32)),
        sa.Column("generator_version", sa.String(64)),
        sa.Column("storage_path", sa.Text),
        sa.Column("manifest_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_artifact_artifact_type", "knowledge_artifact", ["artifact_type"])
    op.create_index("ix_knowledge_artifact_canonical_slug", "knowledge_artifact", ["canonical_slug"], unique=True)
    op.create_index("ix_knowledge_artifact_type_status", "knowledge_artifact", ["artifact_type", "status"])

    op.create_table(
        "artifact_source_link",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("artifact_id", sa.Integer, sa.ForeignKey("knowledge_artifact.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_kind", sa.String(64), nullable=False),
        sa.Column("source_id", sa.Integer, nullable=False),
        sa.Column("support_type", sa.String(32), nullable=False, server_default="primary"),
        sa.Column("notes", sa.Text),
    )
    op.create_index("ix_artifact_source_link_artifact_id", "artifact_source_link", ["artifact_id"])
    op.create_index("ix_artifact_source_link_source_id", "artifact_source_link", ["source_id"])

    op.create_table(
        "knowledge_claim",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("artifact_id", sa.Integer, sa.ForeignKey("knowledge_artifact.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_type", sa.String(32), nullable=False),
        sa.Column("claim_text", sa.Text, nullable=False),
        sa.Column("confidence", sa.String(32)),
        sa.Column("review_status", sa.String(32)),
        sa.Column("conflict_group_id", sa.Integer),
        sa.Column("is_conflicted", sa.Boolean, server_default="false"),
        sa.Column("provenance_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_claim_artifact_id", "knowledge_claim", ["artifact_id"])
    op.create_index("ix_knowledge_claim_conflict_group_id", "knowledge_claim", ["conflict_group_id"])

    op.create_table(
        "entity_registry",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("canonical_name", sa.Text, nullable=False),
        sa.Column("aliases_json", JSONB),
        sa.Column("external_refs_json", JSONB),
        sa.Column("status", sa.String(32)),
    )
    op.create_index("ix_entity_registry_entity_type", "entity_registry", ["entity_type"])
    op.create_index("ix_entity_registry_type_name", "entity_registry", ["entity_type", "canonical_name"])

    op.create_table(
        "artifact_backlink",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("from_artifact_id", sa.Integer, sa.ForeignKey("knowledge_artifact.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_artifact_id", sa.Integer, sa.ForeignKey("knowledge_artifact.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link_type", sa.String(32), nullable=False),
    )
    op.create_index("ix_artifact_backlink_from_artifact_id", "artifact_backlink", ["from_artifact_id"])
    op.create_index("ix_artifact_backlink_to_artifact_id", "artifact_backlink", ["to_artifact_id"])
    op.create_index("ix_artifact_backlink_from_to", "artifact_backlink", ["from_artifact_id", "to_artifact_id"])

    op.create_table(
        "output_release",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("output_type", sa.String(64), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("artifact_id", sa.Integer, sa.ForeignKey("knowledge_artifact.id", ondelete="SET NULL")),
        sa.Column("file_pointer", sa.Text),
        sa.Column("scope_json", JSONB),
        sa.Column("generator_version", sa.String(64)),
        sa.Column("review_status", sa.String(32)),
        sa.Column("released_at", sa.DateTime(timezone=True)),
        sa.Column("file_back_status", sa.String(32)),
    )
    op.create_index("ix_output_release_output_type", "output_release", ["output_type"])
    op.create_index("ix_output_release_artifact_id", "output_release", ["artifact_id"])


def downgrade() -> None:
    op.drop_table("output_release")
    op.drop_table("artifact_backlink")
    op.drop_table("entity_registry")
    op.drop_table("knowledge_claim")
    op.drop_table("artifact_source_link")
    op.drop_table("knowledge_artifact")
