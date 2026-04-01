"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # document_registry
    op.create_table(
        "document_registry",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("external_id", sa.String(256), unique=True, index=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("card_url", sa.Text),
        sa.Column("html_url", sa.Text),
        sa.Column("pdf_url", sa.Text),
        sa.Column("specialty", sa.String(512)),
        sa.Column("age_group", sa.String(128)),
        sa.Column("status", sa.String(128)),
        sa.Column("version_label", sa.String(256)),
        sa.Column("publish_date", sa.String(64)),
        sa.Column("update_date", sa.String(64)),
        sa.Column("source_payload_json", JSONB),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_document_registry_specialty", "document_registry", ["specialty"])
    op.create_index("ix_document_registry_status", "document_registry", ["status"])

    # document_version
    op.create_table(
        "document_version",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("registry_id", sa.Integer, sa.ForeignKey("document_registry.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version_hash", sa.String(128)),
        sa.Column("source_type_primary", sa.String(32)),
        sa.Column("source_type_available", sa.String(128)),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_current", sa.Boolean, default=True),
    )
    op.create_index("ix_document_version_registry_current", "document_version", ["registry_id", "is_current"])

    # source_artifact
    op.create_table(
        "source_artifact",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("document_version_id", sa.Integer, sa.ForeignKey("document_version.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("artifact_type", sa.String(32), nullable=False),
        sa.Column("raw_path", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("content_type", sa.String(128)),
        sa.Column("headers_json", JSONB),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # document_section
    op.create_table(
        "document_section",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("document_version_id", sa.Integer, sa.ForeignKey("document_version.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("section_path", sa.String(512)),
        sa.Column("section_title", sa.Text),
        sa.Column("section_order", sa.Integer, default=0),
        sa.Column("normalizer_version", sa.String(64)),
    )

    # text_fragment
    op.create_table(
        "text_fragment",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("section_id", sa.Integer, sa.ForeignKey("document_section.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("fragment_order", sa.Integer, default=0),
        sa.Column("fragment_type", sa.String(32), default="paragraph"),
        sa.Column("fragment_text", sa.Text, nullable=False),
        sa.Column("stable_id", sa.String(128), unique=True),
    )

    # molecule
    op.create_table(
        "molecule",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("inn_ru", sa.Text, nullable=False, unique=True),
        sa.Column("inn_en", sa.Text),
        sa.Column("atc_code", sa.String(16)),
    )

    # molecule_synonym
    op.create_table(
        "molecule_synonym",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("molecule_id", sa.Integer, sa.ForeignKey("molecule.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("synonym_text", sa.Text, nullable=False),
        sa.Column("source", sa.String(32), default="manual"),
    )

    # clinical_context
    op.create_table(
        "clinical_context",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("disease_name", sa.Text, nullable=False),
        sa.Column("line_of_therapy", sa.String(128)),
        sa.Column("treatment_goal", sa.Text),
        sa.Column("population_json", JSONB),
        sa.Column("context_signature", sa.String(512), unique=True, nullable=False),
        sa.Column("document_version_id", sa.Integer, index=True),
        sa.Column("fragment_id", sa.Integer, index=True),
    )

    # pair_evidence
    op.create_table(
        "pair_evidence",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("context_id", sa.Integer, sa.ForeignKey("clinical_context.id"), nullable=False, index=True),
        sa.Column("molecule_from_id", sa.Integer, sa.ForeignKey("molecule.id"), nullable=False, index=True),
        sa.Column("molecule_to_id", sa.Integer, sa.ForeignKey("molecule.id"), nullable=False, index=True),
        sa.Column("fragment_id", sa.Integer, sa.ForeignKey("text_fragment.id"), nullable=False, index=True),
        sa.Column("relation_type", sa.String(64), nullable=False),
        sa.Column("uur", sa.String(8)),
        sa.Column("udd", sa.String(8)),
        sa.Column("role_score", sa.Float),
        sa.Column("text_score", sa.Float),
        sa.Column("population_score", sa.Float),
        sa.Column("parity_score", sa.Float),
        sa.Column("practical_score", sa.Float),
        sa.Column("penalty", sa.Float),
        sa.Column("final_fragment_score", sa.Float),
        sa.Column("review_status", sa.String(32), default="auto"),
        sa.Column("extractor_version", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # scoring_model_version
    op.create_table(
        "scoring_model_version",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("version_label", sa.String(64), nullable=False, unique=True),
        sa.Column("weights_json", JSONB, nullable=False),
        sa.Column("code_commit_hash", sa.String(64)),
        sa.Column("description", sa.String(512)),
        sa.Column("is_active", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # pair_context_score
    op.create_table(
        "pair_context_score",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("model_version_id", sa.Integer, sa.ForeignKey("scoring_model_version.id"), nullable=False, index=True),
        sa.Column("context_id", sa.Integer, sa.ForeignKey("clinical_context.id"), nullable=False, index=True),
        sa.Column("molecule_from_id", sa.Integer, sa.ForeignKey("molecule.id"), nullable=False),
        sa.Column("molecule_to_id", sa.Integer, sa.ForeignKey("molecule.id"), nullable=False),
        sa.Column("substitution_score", sa.Float),
        sa.Column("confidence_score", sa.Float),
        sa.Column("evidence_count", sa.Integer, default=0),
        sa.Column("explanation_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # matrix_cell
    op.create_table(
        "matrix_cell",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("model_version_id", sa.Integer, sa.ForeignKey("scoring_model_version.id"), nullable=False, index=True),
        sa.Column("scope_type", sa.String(32), default="global"),
        sa.Column("scope_id", sa.String(256)),
        sa.Column("molecule_from_id", sa.Integer, sa.ForeignKey("molecule.id"), nullable=False, index=True),
        sa.Column("molecule_to_id", sa.Integer, sa.ForeignKey("molecule.id"), nullable=False, index=True),
        sa.Column("substitution_score", sa.Float),
        sa.Column("confidence_score", sa.Float),
        sa.Column("contexts_count", sa.Integer, default=0),
        sa.Column("supporting_evidence_count", sa.Integer, default=0),
        sa.Column("explanation_short", sa.Text),
        sa.Column("explanation_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # review_action
    op.create_table(
        "review_action",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("target_id", sa.Integer, nullable=False, index=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("old_value_json", JSONB),
        sa.Column("new_value_json", JSONB),
        sa.Column("reason", sa.Text),
        sa.Column("author", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # pipeline_run
    op.create_table(
        "pipeline_run",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("stage", sa.String(32), nullable=False, index=True),
        sa.Column("run_type", sa.String(32), default="full"),
        sa.Column("status", sa.String(32), default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("discovered_count", sa.Integer, default=0),
        sa.Column("fetched_count", sa.Integer, default=0),
        sa.Column("parsed_count", sa.Integer, default=0),
        sa.Column("failed_count", sa.Integer, default=0),
        sa.Column("stats_json", JSONB),
        sa.Column("error_message", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("pipeline_run")
    op.drop_table("review_action")
    op.drop_table("matrix_cell")
    op.drop_table("pair_context_score")
    op.drop_table("scoring_model_version")
    op.drop_table("pair_evidence")
    op.drop_table("clinical_context")
    op.drop_table("molecule_synonym")
    op.drop_table("molecule")
    op.drop_table("text_fragment")
    op.drop_table("document_section")
    op.drop_table("source_artifact")
    op.drop_table("document_version")
    op.drop_index("ix_document_registry_status", "document_registry")
    op.drop_index("ix_document_registry_specialty", "document_registry")
    op.drop_table("document_registry")
