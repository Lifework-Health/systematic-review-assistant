"""SearchResult_consolidation

Revision ID: 3c121a82c373
Revises: f4c07df39652
Create Date: 2025-04-08 03:00:40.172399+00:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from loguru import logger
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision: str = "3c121a82c373"
down_revision: str | None = "f4c07df39652"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "search_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column("review_id", sa.Uuid(), nullable=False),
        sa.Column(
            "source_db",
            postgresql.ENUM("PUBMED", "SCOPUS", name="searchdatabasesource_enum"),
            nullable=False,
        ),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("doi", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("journal", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("year", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("authors", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.ForeignKeyConstraint(["review_id"], ["systematic_reviews.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "review_id", "source_db", "source_id", name="uq_review_source_id"
        ),
    )
    op.create_index(
        op.f("ix_search_results_doi"), "search_results", ["doi"], unique=False
    )
    op.create_index(
        "ix_search_results_on_keywords_gin",
        "search_results",
        [sa.literal_column("keywords")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_search_results_on_raw_data_gin",
        "search_results",
        [sa.literal_column("raw_data")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_search_results_on_source_metadata_gin",
        "search_results",
        [sa.literal_column("source_metadata")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("ix_search_results_review_id"),
        "search_results",
        ["review_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_search_results_source_db"),
        "search_results",
        ["source_db"],
        unique=False,
    )
    op.create_index(
        op.f("ix_search_results_source_id"),
        "search_results",
        ["source_id"],
        unique=False,
    )

    # --- Move constraint drops BEFORE dropping pubmed_results ---
    try:
        op.drop_constraint(
            "screen_abstract_results_pubmed_result_id_fkey",
            "screen_abstract_results",
            type_="foreignkey",
        )
    except ProgrammingError as e:
        logger.warning(
            f"Constraint screen_abstract_results_pubmed_result_id_fkey not found, skipping drop: {e}"
        )
    # op.drop_constraint(
    #     "screening_resolutions_pubmed_result_id_fkey",
    #     "screening_resolutions",
    #     type_="foreignkey",
    # )
    # --- End moved constraints ---

    op.drop_index(
        "ix_pubmed_results_comprehensive_result_id",
        table_name="pubmed_results",
        if_exists=True,
    )
    op.drop_index(
        "ix_pubmed_results_conservative_result_id",
        table_name="pubmed_results",
        if_exists=True,
    )
    op.drop_index("ix_pubmed_results_pmid", table_name="pubmed_results", if_exists=True)
    op.drop_index(
        "ix_pubmed_results_resolution_id", table_name="pubmed_results", if_exists=True
    )
    op.drop_index(
        "ix_pubmed_results_review_id", table_name="pubmed_results", if_exists=True
    )
    op.drop_table("pubmed_results")

    op.alter_column(
        "log_records",
        "extra",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
    op.alter_column(
        "log_records",
        "record",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
    op.add_column(
        "screen_abstract_results",
        sa.Column("search_result_id", sa.Uuid(), nullable=False),
    )
    op.alter_column(
        "screen_abstract_results",
        "exclusion_reason_categories",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
    op.alter_column(
        "screen_abstract_results",
        "response_metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
    op.drop_index(
        "ix_screen_abstract_results_pubmed_result_id",
        table_name="screen_abstract_results",
    )
    op.create_index(
        op.f("ix_screen_abstract_results_search_result_id"),
        "screen_abstract_results",
        ["search_result_id"],
        unique=False,
    )
    op.create_foreign_key(
        None, "screen_abstract_results", "search_results", ["search_result_id"], ["id"]
    )
    op.drop_column("screen_abstract_results", "pubmed_result_id")
    # op.add_column(
    #     "screening_resolutions",
    #     sa.Column("search_result_id", sa.Uuid(), nullable=False),
    # )
    # op.alter_column(
    #     "screening_resolutions",
    #     "conservative_result_id",
    #     existing_type=sa.UUID(),
    #     nullable=True,
    # )
    # op.alter_column(
    #     "screening_resolutions",
    #     "comprehensive_result_id",
    #     existing_type=sa.UUID(),
    #     nullable=True,
    # )
    # op.drop_index(
    #     "ix_screening_resolutions_on_resolver_include_gin",
    #     table_name="screening_resolutions",
    #     postgresql_using="gin",
    # )
    # op.drop_index(
    #     "ix_screening_resolutions_pubmed_result_id", table_name="screening_resolutions"
    # )
    # op.create_index(
    #     op.f("ix_screening_resolutions_search_result_id"),
    #     "screening_resolutions",
    #     ["search_result_id"],
    #     unique=False,
    # )
    # op.create_foreign_key(
    #     None, "screening_resolutions", "search_results", ["search_result_id"], ["id"]
    # )
    # op.drop_column("screening_resolutions", "pubmed_result_id")
    # op.drop_column("screening_resolutions", "resolver_include")
    op.alter_column(
        "systematic_reviews",
        "inclusion_criteria",
        existing_type=sa.TEXT(),
        nullable=True,
    )
    # ### end Alembic commands ###

    # --- Move constraint drops here to avoid issues with index drops on columns that will be dropped ---
    # op.drop_index(
    #     "ix_pubmed_results_on_resolver_include_gin",
    #     table_name="pubmed_results",
    #     postgresql_using="gin",
    #     if_exists=True,
    # )
    # op.drop_index(
    #     "ix_pubmed_results_resolution_id", table_name="pubmed_results", if_exists=True
    # )
    # op.drop_index(
    #     "ix_pubmed_results_staging_id", table_name="pubmed_results", if_exists=True
    # )
    # op.drop_index(
    #     "ix_screen_abstract_results_pubmed_result_id",
    #     table_name="screen_abstract_results",
    #     if_exists=True,
    # )

    # try:
    #     op.drop_constraint(
    #         "screen_abstract_results_pubmed_result_id_fkey",
    #         "screen_abstract_results",
    #         type_="foreignkey",
    #     )
    # except ProgrammingError as e:
    #     logger.warning(
    #         f"Constraint screen_abstract_results_pubmed_result_id_fkey not found, skipping drop: {e}"
    #     )


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "systematic_reviews",
        "inclusion_criteria",
        existing_type=sa.TEXT(),
        nullable=False,
    )
    op.add_column(
        "screening_resolutions",
        sa.Column(
            "resolver_include",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "screening_resolutions",
        sa.Column("pubmed_result_id", sa.UUID(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(None, "screening_resolutions", type_="foreignkey")
    op.create_foreign_key(
        "screening_resolutions_pubmed_result_id_fkey",
        "screening_resolutions",
        "pubmed_results",
        ["pubmed_result_id"],
        ["id"],
    )
    op.drop_index(
        op.f("ix_screening_resolutions_search_result_id"),
        table_name="screening_resolutions",
    )
    op.create_index(
        "ix_screening_resolutions_pubmed_result_id",
        "screening_resolutions",
        ["pubmed_result_id"],
        unique=False,
    )
    op.create_index(
        "ix_screening_resolutions_on_resolver_include_gin",
        "screening_resolutions",
        ["resolver_include"],
        unique=False,
        postgresql_using="gin",
    )
    op.alter_column(
        "screening_resolutions",
        "comprehensive_result_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.alter_column(
        "screening_resolutions",
        "conservative_result_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.drop_column("screening_resolutions", "search_result_id")
    op.add_column(
        "screen_abstract_results",
        sa.Column("pubmed_result_id", sa.UUID(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(None, "screen_abstract_results", type_="foreignkey")
    op.create_foreign_key(
        "screen_abstract_results_pubmed_result_id_fkey",
        "screen_abstract_results",
        "pubmed_results",
        ["pubmed_result_id"],
        ["id"],
    )
    op.drop_index(
        op.f("ix_screen_abstract_results_search_result_id"),
        table_name="screen_abstract_results",
    )
    op.create_index(
        "ix_screen_abstract_results_pubmed_result_id",
        "screen_abstract_results",
        ["pubmed_result_id"],
        unique=False,
    )
    op.alter_column(
        "screen_abstract_results",
        "response_metadata",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    op.alter_column(
        "screen_abstract_results",
        "exclusion_reason_categories",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    op.drop_column("screen_abstract_results", "search_result_id")
    op.alter_column(
        "log_records",
        "record",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    op.alter_column(
        "log_records",
        "extra",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    op.create_table(
        "pubmed_results",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("timezone('UTC'::text, CURRENT_TIMESTAMP)"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("timezone('UTC'::text, CURRENT_TIMESTAMP)"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("query", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("pmid", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("pmc", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("doi", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("title", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("abstract", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("journal", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("year", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("review_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "conservative_result_id", sa.UUID(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "comprehensive_result_id", sa.UUID(), autoincrement=False, nullable=True
        ),
        sa.Column("resolution_id", sa.UUID(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["comprehensive_result_id"],
            ["screen_abstract_results.id"],
            name="pubmed_results_comprehensive_result_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["conservative_result_id"],
            ["screen_abstract_results.id"],
            name="pubmed_results_conservative_result_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["resolution_id"],
            ["screening_resolutions.id"],
            name="pubmed_results_resolution_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["systematic_reviews.id"],
            name="pubmed_results_review_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pubmed_results_pkey"),
    )
    op.create_index(
        "ix_pubmed_results_review_id", "pubmed_results", ["review_id"], unique=False
    )
    op.create_index(
        "ix_pubmed_results_resolution_id",
        "pubmed_results",
        ["resolution_id"],
        unique=False,
    )
    op.create_index("ix_pubmed_results_pmid", "pubmed_results", ["pmid"], unique=False)
    op.create_index(
        "ix_pubmed_results_conservative_result_id",
        "pubmed_results",
        ["conservative_result_id"],
        unique=False,
    )
    op.create_index(
        "ix_pubmed_results_comprehensive_result_id",
        "pubmed_results",
        ["comprehensive_result_id"],
        unique=False,
    )
    op.drop_index(op.f("ix_search_results_source_id"), table_name="search_results")
    op.drop_index(op.f("ix_search_results_source_db"), table_name="search_results")
    op.drop_index(op.f("ix_search_results_review_id"), table_name="search_results")
    op.drop_index(
        "ix_search_results_on_source_metadata_gin",
        table_name="search_results",
        postgresql_using="gin",
    )
    op.drop_index(
        "ix_search_results_on_raw_data_gin",
        table_name="search_results",
        postgresql_using="gin",
    )
    op.drop_index(
        "ix_search_results_on_keywords_gin",
        table_name="search_results",
        postgresql_using="gin",
    )
    op.drop_index(op.f("ix_search_results_doi"), table_name="search_results")
    op.drop_table("search_results")
    # ### end Alembic commands ###
