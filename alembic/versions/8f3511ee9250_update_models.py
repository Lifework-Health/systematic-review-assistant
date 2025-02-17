"""update models

Revision ID: 8f3511ee9250
Revises: a8b474163c4b
Create Date: 2025-02-16 07:15:51.427262+00:00

"""

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8f3511ee9250"
down_revision: str | None = "a8b474163c4b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "log_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("timestamp", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "level",
            postgresql.ENUM(
                "TRACE",
                "DEBUG",
                "INFO",
                "SUCCESS",
                "WARNING",
                "ERROR",
                "CRITICAL",
                name="loglevel_enum",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("module", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("function", sa.String(length=200), nullable=True),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.Column("thread", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("process", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column(
            "extra",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "exception",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "record",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("review_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["review_id"],
            ["systematic_reviews.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_log_records_level"), "log_records", ["level"], unique=False
    )
    op.create_index(
        op.f("ix_log_records_message"), "log_records", ["message"], unique=False
    )
    op.create_index(
        "ix_log_records_on_exception_gin",
        "log_records",
        [sa.text("exception")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_log_records_on_extra_gin",
        "log_records",
        [sa.text("extra")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("ix_log_records_review_id"), "log_records", ["review_id"], unique=False
    )
    op.create_index(
        op.f("ix_log_records_timestamp"), "log_records", ["timestamp"], unique=False
    )
    op.add_column(
        "screen_abstract_results", sa.Column("trace_id", sa.Uuid(), nullable=True)
    )
    op.create_index(
        op.f("ix_screen_abstract_results_decision"),
        "screen_abstract_results",
        ["decision"],
        unique=False,
    )
    op.create_index(
        "ix_screen_abstract_results_on_exclusion_reason_categories_gin",
        "screen_abstract_results",
        [sa.text("exclusion_reason_categories")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        op.f("ix_screen_abstract_results_screening_strategy"),
        "screen_abstract_results",
        ["screening_strategy"],
        unique=False,
    )
    op.create_index(
        op.f("ix_screen_abstract_results_trace_id"),
        "screen_abstract_results",
        ["trace_id"],
        unique=False,
    )
    criteriaframework_enum = postgresql.ENUM(
        "ECLIPSE",
        "PEO",
        "PICO",
        "PICOS",
        "PICOT",
        "PICOS/T",
        "SPIDER",
        "SPICE",
        name="criteriaframework_enum",
    )
    criteriaframework_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "systematic_reviews",
        sa.Column(
            "criteria_framework",
            postgresql.ENUM(
                "ECLIPSE",
                "PEO",
                "PICO",
                "PICOS",
                "PICOT",
                "PICOS/T",
                "SPIDER",
                "SPICE",
                name="criteriaframework_enum",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "systematic_reviews",
        sa.Column(
            "criteria_framework_answers",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=False,
        ),
    )
    op.add_column(
        "systematic_reviews",
        sa.Column(
            "review_metadata",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=False,
        ),
    )
    op.alter_column(
        "systematic_reviews", "background", existing_type=sa.TEXT(), nullable=True
    )
    op.create_index(
        "ix_systematic_reviews_on_criteria_framework_answers_gin",
        "systematic_reviews",
        [sa.text("criteria_framework_answers")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(
        "ix_systematic_reviews_on_review_metadata_gin",
        "systematic_reviews",
        [sa.text("review_metadata")],
        unique=False,
        postgresql_using="gin",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "ix_systematic_reviews_on_review_metadata_gin",
        table_name="systematic_reviews",
        postgresql_using="gin",
    )
    op.drop_index(
        "ix_systematic_reviews_on_criteria_framework_answers_gin",
        table_name="systematic_reviews",
        postgresql_using="gin",
    )
    op.alter_column(
        "systematic_reviews", "background", existing_type=sa.TEXT(), nullable=False
    )
    op.drop_column("systematic_reviews", "review_metadata")
    op.drop_column("systematic_reviews", "criteria_framework_answers")
    op.drop_column("systematic_reviews", "criteria_framework")
    op.drop_index(
        op.f("ix_screen_abstract_results_trace_id"),
        table_name="screen_abstract_results",
    )
    op.drop_index(
        op.f("ix_screen_abstract_results_screening_strategy"),
        table_name="screen_abstract_results",
    )
    op.drop_index(
        "ix_screen_abstract_results_on_exclusion_reason_categories_gin",
        table_name="screen_abstract_results",
        postgresql_using="gin",
    )
    op.drop_index(
        op.f("ix_screen_abstract_results_decision"),
        table_name="screen_abstract_results",
    )
    op.drop_column("screen_abstract_results", "trace_id")
    op.drop_index(op.f("ix_log_records_timestamp"), table_name="log_records")
    op.drop_index(op.f("ix_log_records_review_id"), table_name="log_records")
    op.drop_index(
        "ix_log_records_on_extra_gin", table_name="log_records", postgresql_using="gin"
    )
    op.drop_index(
        "ix_log_records_on_exception_gin",
        table_name="log_records",
        postgresql_using="gin",
    )
    op.drop_index(op.f("ix_log_records_message"), table_name="log_records")
    op.drop_index(op.f("ix_log_records_level"), table_name="log_records")
    op.drop_table("log_records")
    # ### end Alembic commands ###
