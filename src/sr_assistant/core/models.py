# src/sr_assistant/core/models/base.py
"""SQLModel/Alchemy models for SRA.

These are mostly for DB R/W and abstracted away from the
application layer which uses Pydantic schemas. SQLModel
has limitations and moving forward we'll switch to
SQLAlchemy and fully separate data and schema/validation/
serialization.
"""

import enum
import typing as t
import uuid
from collections.abc import Mapping, MutableMapping, Sequence
from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_pg
from pydantic import ConfigDict, JsonValue
from pydantic.types import PositiveInt
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel  # type: ignore

from sr_assistant.core.types import (
    CriteriaFramework,
    LogLevel,
    ScreeningDecisionType,
    ScreeningStrategyType,
    UtcDatetime,
)


def add_gin_index(table_name: str, column_name: str) -> sa.Index:
    """Add a GIN index to a JSONB column."""
    return sa.Index(
        f"ix_{table_name}_on_{column_name}_gin",
        sa.text(column_name),
        postgresql_using="gin",
    )


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    """Get values for enum."""
    return [member.value for member in enum_class]


class SQLModelBase(AsyncAttrs, SQLModel):
    """Base SQLModel with ``awaitable_attrs`` mixin attribute.

    Attributes:
        awaitable_attrs: SQLAlchemy proxy mixin that makes all attributes awaitable.
    """

    model_config = ConfigDict(  # type: ignore
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        use_attribute_docstrings=True,
    )


Base = SQLModelBase


class SystematicReview(SQLModelBase, table=True):
    """Systematic review model.

    A systematic review project containing the research question, background,
    and inclusion/exclusion criteria. These are combined with search results to
    generate input to screening chain/agent.

    Notes:
        - In Python, pubmed_results field links to list of PubMedResult which again
          have conservative_result and comprehensive_result fields pointing to the
          abstracts screening results table.

    Todo:
        - PICO, etc., need to figure out UI updating by agent ...
    """

    _tablename: t.ClassVar[t.Literal["systematic_reviews"]] = "systematic_reviews"

    __tablename__ = _tablename  # pyright: ignore # type: ignore

    __table_args__ = (
        add_gin_index(_tablename, "criteria_framework_answers"),
        add_gin_index(_tablename, "review_metadata"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
    )
    """Database generated UTC timestamp when `SystematicReview` was created."""

    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            onupdate=sa.func.now(),
            nullable=True,
        ),
    )
    """Database generated UTC timestamp when this `SystematicReview` was updated."""

    background: str = Field(
        default="",
        sa_column=sa.Column(sa.Text()),
    )
    """Background context for the systematic review."""

    research_question: str = Field(
        sa_column=sa.Column(sa.Text(), nullable=False),
    )
    """The research question."""

    # TODO: sort this out, update ui, these replace inclusion_criteria
    # This enum should have properties returning UI values and descriptions such that
    # a tabbed/selectbox form can be created dynamically, and preferably drafted by AI
    criteria_framework: CriteriaFramework | None = Field(
        default=None,
        description="The criteria framework.",
        sa_column=sa.Column(
            type_=sa_pg.ENUM(
                CriteriaFramework,
                name="criteriaframework_enum",
                values_callable=enum_values,
            ),
            nullable=True,
        ),
    )
    """The criteria framework."""

    criteria_framework_answers: MutableMapping[str, JsonValue] = Field(
        default_factory=dict,
        sa_column=sa.Column(sa_pg.JSONB(none_as_null=True), nullable=False),
    )
    """Answers to the criteria framework."""

    inclusion_criteria: str | None = Field(
        description="Inclusion criteria. To be replaced by above framework fields.",
        sa_column=sa.Column(sa.Text(), nullable=True),
    )
    """Inclusion criteria."""

    exclusion_criteria: str = Field(
        description="The exclusion criteria for studies",
        sa_column=sa.Column(sa.Text(), nullable=False),
    )
    """The exclusion criteria for studies."""

    # One review has many PubMedResults
    pubmed_results: Mapped[list["PubMedResult"]] = Relationship(
        back_populates="review",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    """PubMed search results for the review."""

    screen_abstract_results: Mapped[list["ScreenAbstractResult"]] = Relationship(
        back_populates="review",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    """Screening results for the review."""

    log_records: Mapped[list["LogRecord"]] = Relationship(
        back_populates="review",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    """Log records for the review."""

    screening_resolutions: Mapped[list["ScreeningResolution"]] = Relationship(
        back_populates="review"
    )
    """Screening resolutions associated with this review."""

    review_metadata: MutableMapping[str, JsonValue] = Field(
        default_factory=dict,
        sa_column=sa.Column(sa_pg.JSONB(none_as_null=True), nullable=False),
    )
    """Any metadata associated with the review."""


class PubMedResult(SQLModelBase, table=True):
    """PubMed search result.

    Stores both search info and result in one table for prototype simplicity.

    Todo:
        - Maybe strategies should be just enumrated to avoid hardcoding in schema?
    """

    _tablename: t.ClassVar[t.Literal["pubmed_results"]] = "pubmed_results"

    __tablename__ = _tablename  # pyright: ignore # type: ignore

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        description="Database generated UTC timestamp when `PubMedResult` was created.",
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
    )
    """Database generated UTC timestamp when `PubMedResult` was created."""

    updated_at: datetime | None = Field(
        default=None,
        description="Database generated UTC timestamp when this `PubMedResult` was updated.",
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            onupdate=sa.func.now(),
            nullable=True,
        ),
    )
    """Database generated UTC timestamp when this `PubMedResult` was updated."""

    query: str = Field(
        description="PubMed search query",
        title="Query",
        sa_column=sa.Column(sa.Text(), nullable=False),
        schema_extra={"example": "(cancer) AND (immunotherapy) AND (clinical trial)"},
    )
    """PubMed search query."""

    # Article info
    pmid: str = Field(
        index=True,
        title="PMID",
        schema_extra={"example": "39844819"},
    )
    """PubMed ID."""

    pmc: str | None = Field(
        default=None,
        title="PMC ID",
        schema_extra={"example": "PMC11753851"},
    )
    """PubMed Central ID if available."""

    doi: str | None = Field(
        default=None,
        title="DOI",
        schema_extra={"example": "10.1155/jimr/5845167"},
    )
    """Digital Object Identifier (DOI) if available."""

    title: str = Field(title="Title")
    abstract: str = Field(
        title="Abstract",
        sa_column=sa.Column(sa.Text(), nullable=False),
    )
    """Abstract of the article."""

    journal: str = Field(title="Journal")
    """Journal of the article."""

    year: str = Field(title="Year of publication")
    """Year of publication."""

    # One PubMedResult belongs to one SystematicReview
    review_id: uuid.UUID = Field(
        foreign_key="systematic_reviews.id", ondelete="CASCADE", index=True
    )
    review: Mapped["SystematicReview"] = Relationship(
        back_populates="pubmed_results",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    resolution_id: uuid.UUID | None = Field(
        default=None, foreign_key="screening_resolutions.id", nullable=True, index=True
    )
    # One PubMedResult has two ScreenAbstractResults (conservative and comprehensive)
    # Circular relationship that causes Alembic warnings. AI says can be ignored since
    # valid business reason, but who trusts AI?
    conservative_result_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="screen_abstract_results.id",
        index=True,
        # sa_column=sa.Column(sa.UUID, sa.ForeignKey("screen_abstract_results.id"), index=True, nullable=True),
    )
    conservative_result: Mapped["ScreenAbstractResult"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "PubMedResult.conservative_result_id",
            "lazy": "selectin",
            "post_update": True,  # break the cycle
        }
    )

    comprehensive_result_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="screen_abstract_results.id",
        index=True,
        # sa_column=sa.Column(sa.UUID, sa.ForeignKey("screen_abstract_results.id"), index=True, nullable=True),
    )
    comprehensive_result: Mapped["ScreenAbstractResult"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "PubMedResult.comprehensive_result_id",
            "lazy": "selectin",
            "post_update": True,  # break the cycle
        }
    )

    resolution: Mapped["ScreeningResolution"] = Relationship(
        sa_relationship_kwargs={
            "uselist": False,  # Mark as one-to-one/scalar
            "foreign_keys": "[PubMedResult.resolution_id]",  # Specify the FK for this relationship
            "primaryjoin": None,  # Prevent automatic join condition determination
        },
    )


class ScreeningResolution(SQLModelBase, table=True):
    _tablename = "screening_resolutions"

    __tablename__ = _tablename  # pyright: ignore # type: ignore

    __table_args__ = (add_gin_index(_tablename, "response_metadata"),)

    # --- Fields ---
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            onupdate=sa.func.now(),
            nullable=True,
        ),
    )
    pubmed_result_id: uuid.UUID = Field(foreign_key="pubmed_results.id", index=True)
    review_id: uuid.UUID = Field(foreign_key="systematic_reviews.id", index=True)
    conservative_result_id: uuid.UUID = Field(
        foreign_key="screen_abstract_results.id", index=True
    )
    comprehensive_result_id: uuid.UUID = Field(
        foreign_key="screen_abstract_results.id", index=True
    )
    resolver_decision: ScreeningDecisionType = Field(
        sa_column=sa.Column(
            sa_pg.ENUM(
                ScreeningDecisionType,
                name="screeningdecisiontype",
                values_callable=enum_values,
                create_type=False,
            ),
            nullable=False,
            index=True,
        )
    )
    resolver_reasoning: str = Field(sa_column=sa.Column(sa.Text(), nullable=False))
    resolver_confidence_score: float = Field(ge=0.0, le=1.0)
    resolver_model_name: str | None = Field(default=None)
    response_metadata: Mapping[str, JsonValue] | None = Field(
        default_factory=dict,
        sa_column=sa.Column(sa_pg.JSONB(none_as_null=True), nullable=False),
    )
    start_time: datetime | None = Field(
        default=None, sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True)
    )
    end_time: datetime | None = Field(
        default=None, sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True)
    )
    trace_id: uuid.UUID | None = Field(default=None, index=True, nullable=True)

    # --- Relationships ---
    pubmed_result: Mapped["PubMedResult"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ScreeningResolution.pubmed_result_id]"
        }
    )
    review: Mapped["SystematicReview"] = Relationship(
        back_populates="screening_resolutions",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[ScreeningResolution.review_id]",
        },
    )
    # Add relationships to load the actual abstract results
    conservative_result: Mapped["ScreenAbstractResult"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ScreeningResolution.conservative_result_id]",
            "lazy": "selectin",
            "viewonly": True,  # Avoids potential conflicts with PubMedResult relationships
        }
    )
    comprehensive_result: Mapped["ScreenAbstractResult"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ScreeningResolution.comprehensive_result_id]",
            "lazy": "selectin",
            "viewonly": True,  # Avoids potential conflicts with PubMedResult relationships
        }
    )


class ScreenAbstractResult(SQLModelBase, table=True):
    """Abstract screening decision model.

    Tracks the screening decisions for each paper in the review.

    Attributes:
        decision: ScreeningDecisionType
        confidence_score: float
        rationale: str
        extracted_quotes: list[str]
        exclusion_reason_categories: ExclusionReasons
        id: uuid.UUID (run id)
        review_id: uuid.UUID
        pubmed_result_id: uuid.UUID
        trace_id: uuid.UUID
        model_name: str
        start_time: datetime (UTC)
        end_time: datetime (UTC)
        response_metadata: dict[str, JsonValue]
    """

    _tablename: t.ClassVar[t.Literal["screen_abstract_results"]] = (
        "screen_abstract_results"
    )

    __tablename__ = _tablename  # pyright: ignore # type: ignore

    __table_args__ = (add_gin_index(_tablename, "exclusion_reason_categories"),)

    id: uuid.UUID = Field(
        primary_key=True,
        description="Should be the run_id of the child-child `langsmith.RunTree`, populated by the chain `on_end` listener.",
    )
    created_at: datetime | None = Field(
        default=None,
        description="Database generated UTC timestamp",
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        description="Database generated UTC timestamp",
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            server_default=sa.text("TIMEZONE('UTC', CURRENT_TIMESTAMP)"),
            onupdate=sa.func.now(),
            nullable=True,
        ),
    )
    # Screening decision fields
    decision: ScreeningDecisionType = Field(
        description="Whether to include or exclude the paper, or mark as uncertain",
        sa_column=sa.Column(
            type_=sa_pg.ENUM(
                ScreeningDecisionType,
                name="screeningdecisiontype",
                values_callable=enum_values,
            ),
            nullable=False,
            index=True,
        ),
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="The confidence score for the decision. [0.0, 1.0].",
    )
    rationale: str = Field(
        description="Rationale for the screening decision",
        sa_column=sa.Column(sa.Text(), nullable=False),
    )
    extracted_quotes: Sequence[str] | None = Field(
        default=None,
        description="Supporting quotes from the title/abstract. Can be omitted if uncertain.",
        sa_column=sa.Column(sa_pg.ARRAY(sa.Text()), nullable=True),
    )
    exclusion_reason_categories: Mapping[str, list[str]] = Field(
        default_factory=dict,
        description="The PRISMA exclusion reason categories for the decision. This complements the 'rationale' field.",
        sa_column=sa.Column(sa_pg.JSONB(none_as_null=True)),
    )
    # Injected fields
    trace_id: uuid.UUID | None = Field(
        default=None,
        description="trace_id of the `RunTree` with which the listener was invoked. Populated by the chain `on_end` listener.",
        index=True,
    )
    # Screening decision fields
    start_time: datetime | None = Field(
        default=None,
        description="Chain/graph invocation start time.",
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    end_time: datetime | None = Field(
        default=None,
        description="Chain/graph invocation end time.",
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    screening_strategy: ScreeningStrategyType = Field(
        description="Currently either 'compherensive' or 'conservative'. Maps to kind of prompt used.",
        sa_column=sa.Column(
            type_=sa_pg.ENUM(
                ScreeningStrategyType,
                name="screeningstrategytype",
                values_callable=enum_values,
            ),
            nullable=False,
            index=True,
        ),
    )
    model_name: str = Field(
        description="The LangChain model name that generated this response.",
    )
    response_metadata: Mapping[str, JsonValue] | None = Field(
        default_factory=dict,
        description="Metadata from the chain/graph invocation.",
        sa_column=sa.Column(sa_pg.JSONB(none_as_null=True), nullable=True),
    )

    # Screening Result is associated with one review
    review_id: uuid.UUID = Field(foreign_key="systematic_reviews.id", index=True)
    # Each ScreenAbstractResult belongs to one Review
    review: Mapped["SystematicReview"] = Relationship(
        back_populates="screen_abstract_results",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    # Screening Result is associated with one PubMedResult
    pubmed_result_id: uuid.UUID = Field(
        description="The PubMed result associated with this result",
        foreign_key="pubmed_results.id",
        index=True,
    )
    # Each ScreenAbstractResult belongs to one PubMedResult. Relationship other way is
    # configured in PubMedResult. Key must be fully qualified string, bare field works
    # in SA with mapped columns but not supported by SQLModel.
    #
    # Note: This creates a circular reference, SA post_update is supposed to help with
    # that but Alembic still warns about it. These relationships are needed both ways
    # so not much to do about it?
    pubmed_result: Mapped["PubMedResult"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "ScreenAbstractResult.pubmed_result_id",
        },
    )


class LogRecord(SQLModelBase, table=True):
    """Model for storing app log records."""

    _tablename: t.ClassVar[t.Literal["log_records"]] = "log_records"

    __tablename__ = _tablename  # pyright: ignore # type: ignore

    __table_args__ = (
        add_gin_index(_tablename, "extra"),
        add_gin_index(_tablename, "exception"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: UtcDatetime = Field(
        sa_column=sa.Column(sa_pg.TIMESTAMP(timezone=True), nullable=False, index=True)
    )
    level: LogLevel = Field(
        sa_column=sa.Column(
            type_=sa_pg.ENUM(
                LogLevel, name="loglevel_enum", values_callable=enum_values
            ),
            nullable=False,
            index=True,
        ),
    )
    message: str = Field(sa_column=sa.Column(sa.Text(), nullable=False))
    module: str | None = Field(
        default=None, sa_column=sa.Column(sa.String(100), default=None, nullable=True)
    )
    name: str | None = Field(
        default=None, sa_column=sa.Column(sa.String(100), default=None, nullable=True)
    )
    function: str | None = Field(
        default=None, sa_column=sa.Column(sa.String(200), default=None, nullable=True)
    )
    line: PositiveInt | None = Field(
        default=None, sa_column=sa.Column(sa.Integer(), default=None, nullable=True)
    )
    thread: str | None = Field(default=None, description="{thread.name}:{thread.id}")
    process: str | None = Field(default=None, description="{process.name}:{process.id}")
    extra: Mapping[str, JsonValue] = Field(
        default_factory=dict,
        description="User provided extra context. Has a GIN index.",
        sa_column=sa.Column(sa_pg.JSONB(none_as_null=True)),
    )
    exception: Mapping[str, JsonValue] | None = Field(
        default_factory=dict,
        description="Exception information. Has a GIN index",
        sa_column=sa.Column(sa_pg.JSONB(none_as_null=True), nullable=True),
    )
    record: Mapping[str, JsonValue] = Field(
        default_factory=dict,
        description="This is everything available in the record and context.",
        sa_column=sa.Column(sa_pg.JSONB(none_as_null=True)),
    )
    review_id: uuid.UUID | None = Field(
        default=None,
        description="Read from extra by the model_validator or st state, or by sink. None if not related to a review.",
        sa_column=sa.Column(
            sa.UUID,
            sa.ForeignKey("systematic_reviews.id"),
            default=None,
            index=True,
            nullable=True,
        ),
    )
    review: Mapped["SystematicReview"] = Relationship(
        back_populates="log_records",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    # @model_validator(mode="after")
    # def _set_review_id(self) -> t.Self:
    #    if not self.review_id:
    #        review_id = self.extra.get("review_id")
    #        if not ut.is_uuid(review_id) and ut.in_streamlit():
    #            st_review_id = st.session_state.review_id
    #            if not ut.is_uuid(st_review_id):
    #                review_obj = st.session_state.review
    #                if isinstance(review_obj, SystematicReview):
    #                    review_id = review_obj.id
    #        if (version := ut.is_uuid(review_id)) and version > 0 and version < 6:
    #            review_id = t.cast((str | uuid.UUID), review_id)
    #            self.review_id = (
    #                review_id if isinstance(review_id, uuid.UUID) else uuid.UUID(review_id)
    #            )
    #            logger.info(f"Setting review_id: {self.review_id}")
    #        elif version == 6 and version <= 8:
    #            review_id = t.cast((str | uuid6.UUID), review_id)
    #            self.review_id = (
    #                review_id if isinstance(review_id, uuid6.UUID) else uuid6.UUID(review_id)
    #            )
    #            logger.info(f"Setting review_id: {self.review_id}")
    #    return self
