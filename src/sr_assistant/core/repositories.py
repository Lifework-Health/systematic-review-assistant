"""Synchronous repository implementations for systematic review models.

This module provides sync repositories for database operations using SQLModel.
Includes examples for common operations and complex queries including JSONB.

Note:
    - All repositories use a sessionmaker factory assigned as self.session_factory.

      ``with self.session_factory.begin() as session``:
            - Executes the query within a session.
            - Commits the session.
            - Rollbacks the session on error.
            - DOES NOT SUPPORT MANUAL ``session.commit()``
            - Cannot be used when ``session.refresh()`` is needed.

      ``with self.session_factory() as session``:
            - No automatic commit/rollback
            - Can use ``session.commit()`` and ``session.refresh()`` manually.

    - Async repositories are in `sr_assistant.core.repositories_async`.

Examples:
    Basic repository usage:

    ```python
    # Initialize repository
    review_repo = SystematicReviewRepository()

    # Create new review
    review = SystematicReview(
        research_question="What is the effectiveness of...",
        inclusion_criteria="RCTs published after 2010...",
        exclusion_criteria="Case studies, non-English...",
    )
    created = review_repo.add(review)

    # Get with relationships
    review_with_search_results = review_repo.get_with_pubmed_results(created.id)
    full_review = review_repo.get_with_all(created.id) # search, logs, screening results
    full_review.pubmed_results ...
    full_review.screen_abstract_results ...
    full_review.log_records ...
    ```
"""

from __future__ import annotations

import types
import typing as t

from loguru import logger
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel import and_, col, delete, or_, select

from sr_assistant.app.database import SQLModelSession, session_factory, sessionmaker
from sr_assistant.core.models import (
    Base,
    LogRecord,
    PubMedResult,
    ScreenAbstractResult,
    ScreeningResolution,
    SystematicReview,
)
from sr_assistant.core.schemas import ExclusionReasons
from sr_assistant.core.types import LogLevel, ScreeningStrategyType
from sr_assistant.step2.pubmed_integration import (
    extract_article_info,  # TODO move to app.pubmed_integration
)

if t.TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from pydantic.types import JsonValue
    from sqlmodel.sql.expression import SelectOfScalar


class RepositoryError(Exception):
    """Base exception for persistence layer failures."""


class ConstraintViolationError(RepositoryError):
    """Database constraint violation (unique constraint, foreign key, etc.)."""


class RecordNotFoundError(RepositoryError):
    """Requested record was not found in the database."""


class BaseRepository[T: Base]:
    """Base repository implementing common database operations.

    Args:
        session_factory: SQLAlchemy sessionmaker instance

    Attributes:
        model_cls: SQLModel class this repository manages

    Raises:
        ConstraintViolationError: On database constraint violations
        RecordNotFoundError: When a requested record is not found
        RepositoryError: On other database errors
    """

    def __init__(
        self,
        session_factory: sessionmaker[SQLModelSession] = session_factory,
    ) -> None:
        """Initialize repository with session factory."""
        self.session_factory = session_factory

    @property
    def model_cls(self) -> type[T]:
        """Get the model class associated with the repository."""
        return t.get_args(types.get_original_bases(type(self))[0])[0]

    def _construct_get_stmt(self, id: uuid.UUID) -> SelectOfScalar[T]:
        return select(self.model_cls).where(self.model_cls.id == id)  # pyright: ignore [reportAttributeAccessIssue]

    def get_by_id(self, id: uuid.UUID) -> T | None:
        """Get a record by its ID."""
        try:
            with self.session_factory.begin() as session:
                return session.exec(self._construct_get_stmt(id)).first()
        except SQLAlchemyError as exc:
            msg = f"Database error in get_by_id for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_all(self, limit: int | None = None) -> Sequence[T]:
        """Get all records with optional limit."""
        try:
            with self.session_factory.begin() as session:
                query = select(self.model_cls)
                if limit is not None:
                    query = query.limit(limit)
                return list(session.exec(query))
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch all records for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def _construct_list_stmt(self, **filters: dict[str, t.Any]) -> SelectOfScalar[T]:
        stmt = select(self.model_cls)
        where_clauses = []
        for c, v in filters.items():
            if not hasattr(self.model_cls, c):
                msg = f"Invalid column name {c}"
                logger.warning(msg)
                raise ValueError(msg)
            where_clauses.append(getattr(self.model_cls, c) == v)

        if len(where_clauses) == 1:
            stmt = stmt.where(where_clauses[0])
        elif len(where_clauses) > 1:
            stmt = stmt.where(and_(*where_clauses))
        return stmt

    def list(self, **filters: dict[str, t.Any]) -> Sequence[T]:
        """List records matching the filters. ``model_fiel``, ``value`` pairs.

        Examples:
            >>> repo = SystematicReviewRepository()
            >>> repo.list(dict(criteria_framework="PICO"))
        """
        try:
            stmt = self._construct_list_stmt(**filters)
            with self.session_factory.begin() as session:
                return session.exec(stmt).all()
        except SQLAlchemyError as exc:
            msg = (
                f"Failed to fetch {self.model_cls.__name__} by response metadata: {exc}"
            )
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def add(self, record: T) -> T:
        """Add a new record."""
        try:
            with self.session_factory() as session:
                session.add(record)
                session.commit()
                session.refresh(record)
                return record
        except IntegrityError as exc:
            msg = f"Failed to add {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise ConstraintViolationError(msg) from exc
        except SQLAlchemyError as exc:
            msg = f"Failed to add {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def add_all(self, objs: Sequence[T]) -> Sequence[T]:
        """Add multiple records at once."""
        try:
            with self.session_factory() as session:
                session.add_all(objs)
                session.commit()
                for o in objs:
                    session.refresh(o)
                return objs
        except IntegrityError as exc:
            msg = f"Failed to add multiple {self.model_cls.__name__} records: {exc}"
            logger.exception(msg)
            raise ConstraintViolationError(msg) from exc
        except SQLAlchemyError as exc:
            msg = f"Failed to add multiple {self.model_cls.__name__} records: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def update(self, record: T) -> T:
        """Update an existing record."""
        if not record.id:  # type: ignore
            msg = f"{self.model_cls.__name__} has no id"
            raise ValueError(msg)

        try:
            with self.session_factory.begin() as session:
                # First check if record exists
                existing = session.get(self.model_cls, record.id)  # type: ignore
                if not existing:
                    msg = f"{self.model_cls.__name__} with id {record.id} not found"  # type: ignore [attr-defined] # id exists on Base subclasses
                    logger.warning(msg)
                    raise RecordNotFoundError(msg)

                # Merge the updated record
                assert record not in session  # noqa: S101
                return session.merge(record)
        except IntegrityError as exc:
            msg = f"Database constraint violation in update for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise ConstraintViolationError(msg) from exc
        except SQLAlchemyError as exc:
            msg = f"Database error in update for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def delete(self, id: uuid.UUID) -> None:
        """Delete a record by ID."""
        try:
            record = self.get_by_id(id)
            if record is None:
                msg = f"{self.model_cls.__name__} with id {id} not found"
                logger.warning(msg)
                raise RecordNotFoundError(msg)

            with self.session_factory.begin() as session:
                session.delete(record)
        except IntegrityError as exc:
            msg = f"Database constraint violation in delete for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise ConstraintViolationError(msg) from exc
        except SQLAlchemyError as exc:
            msg = f"Database error in delete for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc


class SystematicReviewRepository(BaseRepository[SystematicReview]):
    """Repository for SystematicReview model operations.

    Examples:
        ```python
        repo = SystematicReviewRepository()

        # Get review with all relationships
        review = repo.get_with_pubmed_results(review_id)

        # Access relationships
        for result in review.pubmed_results:
            print(f"Title: {result.title}")
            if result.conservative_result:
                print(f"Conservative: {result.conservative_result.decision}")
            if result.comprehensive_result:
                print(f"Comprehensive: {result.comprehensive_result.decision}")
        ```
    """

    def get_with_pubmed_results(self, id: uuid.UUID) -> SystematicReview | None:
        """Get a review with its PubMed results and screening results loaded."""
        try:
            with self.session_factory.begin() as session:
                query = (
                    select(self.model_cls)
                    .where(self.model_cls.id == id)
                    .options(
                        selectinload(self.model_cls.pubmed_results),
                    )
                )
                return session.exec(query).first()
        except SQLAlchemyError as exc:
            msg = f"Database error in get_with_pubmed_results for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_with_all(self, id: uuid.UUID) -> SystematicReview | None:
        """Get a review with its PubMed results, screening results, and log records loaded."""
        try:
            with self.session_factory.begin() as session:
                query = (
                    select(self.model_cls)
                    .where(self.model_cls.id == id)
                    .options(
                        selectinload(self.model_cls.pubmed_results),
                        selectinload(self.model_cls.screen_abstract_results),
                        selectinload(self.model_cls.log_records),
                    )
                )
                return session.exec(query).first()
        except SQLAlchemyError as exc:
            msg = f"Database error in get_with_all for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc


class PubMedResultRepository(BaseRepository[PubMedResult]):
    """Repository for PubMedResult model operations.

    Examples:
        ```python
        repo = PubMedResultRepository()

        # Get all results for a review
        results = repo.get_by_review_id(review_id)

        # Get with screening results
        result = repo.get_with_screening_results(pubmed_id)

        # Get results by screening strategy
        conservative = repo.get_by_screening_strategy(
            review_id, ScreeningStrategyType.CONSERVATIVE
        )
        ```
    """

    def get_by_review_id(self, review_id: uuid.UUID) -> Sequence[PubMedResult]:
        """Get all PubMed results for a review."""
        try:
            with self.session_factory.begin() as session:
                query = (
                    select(self.model_cls)
                    .where(self.model_cls.review_id == review_id)
                    .options(
                        selectinload(self.model_cls.review),
                        selectinload(self.model_cls.conservative_result),
                        selectinload(self.model_cls.comprehensive_result),
                    )
                )
                return list(session.exec(query))
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch PubMed results for review {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_with_screening_results(self, id: uuid.UUID) -> PubMedResult | None:
        """Get a PubMed result with both screening results loaded."""
        try:
            with self.session_factory.begin() as session:
                query = (
                    select(self.model_cls)
                    .where(self.model_cls.id == id)
                    .options(
                        selectinload(self.model_cls.conservative_result),
                        selectinload(self.model_cls.comprehensive_result),
                    )
                )
                return session.exec(query).first()
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch PubMed result with screening results for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_by_screening_strategy(
        self,
        review_id: uuid.UUID,
        strategy: ScreeningStrategyType,
    ) -> list[PubMedResult]:
        """Get PubMed results that have a specific screening strategy result."""
        try:
            with self.session_factory.begin() as session:
                query = select(self.model_cls).where(
                    self.model_cls.review_id == review_id
                )

                if strategy == ScreeningStrategyType.CONSERVATIVE:
                    query = query.where(
                        col(self.model_cls.conservative_result_id).is_not(None)
                    )
                    query = query.options(
                        selectinload(self.model_cls.conservative_result)
                    )
                else:
                    query = query.where(
                        col(self.model_cls.comprehensive_result_id).is_not(None)
                    )
                    query = query.options(
                        selectinload(self.model_cls.comprehensive_result)
                    )

                return list(session.exec(query))
        except SQLAlchemyError as exc:
            msg = f"Database error in get_by_screening_strategy for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def store_results(
        self, review_id: uuid.UUID, query: str, records: dict[str, t.Any]
    ) -> Sequence[PubMedResult]:
        """Store PubMed search results.

        Args:
            review_id (uuid.UUID): ID of the review the results belong to.
            query (str): Query used to search PubMed.
            records (dict[str, t.Any]): Search results from PubMed.

        Returns:
            Sequence[PubMedResult]: List of stored PubMed results.
        """
        results = []
        for record in records["PubmedArticle"]:
            try:
                article_info = extract_article_info(record)
                if not article_info:
                    continue
                result = PubMedResult(
                    review_id=review_id,
                    query=query,
                    pmid=article_info["pmid"],
                    pmc=article_info["pmc"],
                    doi=article_info["doi"],
                    title=article_info["title"],
                    abstract=article_info["abstract"],
                    journal=article_info["journal"],
                    year=article_info["year"],
                )
                logger.info(f"Storing PubMed result: {result}")
                with self.session_factory() as session:
                    session.add(result)
                    session.commit()
                    session.refresh(result)
                    results.append(result)
            except Exception:
                msg = f"Failed to extract article info from record: {record!r}"
                logger.exception(msg)
                continue

        if not results:
            return []

        logger.info(f"Stored {len(results)} PubMed results for review {review_id}")
        return results

    def get_by_pmid(self, pmid: str, review_id: uuid.UUID) -> PubMedResult | None:
        """Get a PubMed result by its PMID."""
        try:
            with self.session_factory.begin() as session:
                query = select(self.model_cls).where(
                    self.model_cls.pmid == pmid, self.model_cls.review_id == review_id
                )
                return session.exec(query).first()
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch PubMed result for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def delete_by_review_id(self, review_id: uuid.UUID) -> None:
        """Delete all PubMed results for a review."""
        try:
            with self.session_factory.begin() as session:
                query = delete(self.model_cls).where(
                    col(self.model_cls.review_id) == review_id
                )
                session.exec(query)  # pyright: ignore[reportCallIssue,reportArgumentType] exec missing overload, but works
        except SQLAlchemyError as exc:
            msg = f"Failed to delete PubMed results for review {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc


class ScreenAbstractResultRepository(BaseRepository[ScreenAbstractResult]):
    """Repository for ScreenAbstractResult model operations.

    Examples:
        ```python
        repo = ScreenAbstractResultRepository()

        # Get all results for a review
        results = repo.get_by_review_id(review_id)

        # Get results by strategy
        conservative = repo.get_by_strategy(
            review_id, ScreeningStrategyType.CONSERVATIVE
        )

        # Query by JSONB fields (exclusion reasons)
        wrong_population = repo.get_by_exclusion_category(
            review_id, "population_exclusion_reasons"
        )

        # Complex JSONB query
        results = repo.get_by_response_metadata(
            review_id, {"model": "gpt-4", "temperature": 0.0}
        )
        ```
    """

    def get_by_review_id(self, review_id: uuid.UUID) -> list[ScreenAbstractResult]:
        """Get all screening results for a review."""
        try:
            with self.session_factory.begin() as session:
                query = (
                    select(self.model_cls)
                    .where(self.model_cls.review_id == review_id)
                    .options(selectinload(self.model_cls.pubmed_result))
                )
                return list(session.exec(query))
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch screening results for review {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_by_pubmed_result(
        self,
        review_id: uuid.UUID,
        pubmed_result_id: uuid.UUID,
    ) -> list[ScreenAbstractResult]:
        """Get screening results for a specific PubMed result."""
        try:
            with self.session_factory.begin() as session:
                query = (
                    select(self.model_cls)
                    .where(
                        self.model_cls.review_id == review_id,
                        self.model_cls.pubmed_result_id == pubmed_result_id,
                    )
                    .options(selectinload(self.model_cls.pubmed_result))
                )
                return list(session.exec(query))
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch screening results for PubMed result {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_by_strategy(
        self,
        review_id: uuid.UUID,
        strategy: ScreeningStrategyType,
    ) -> list[ScreenAbstractResult]:
        """Get screening results for a specific strategy."""
        try:
            with self.session_factory.begin() as session:
                query = (
                    select(self.model_cls)
                    .where(
                        self.model_cls.review_id == review_id,
                        self.model_cls.screening_strategy == strategy,
                    )
                    .options(selectinload(self.model_cls.pubmed_result))
                )
                return list(session.exec(query))
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch screening results by strategy for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_by_exclusion_category(
        self,
        review_id: uuid.UUID,
        exclusion_reason: str,
    ) -> list[ScreenAbstractResult]:
        """Get results where any exclusion category list contains the given reason.

        Args:
            review_id: Review ID to filter by
            exclusion_reason: The specific exclusion reason to search for, e.g. "Non-human subjects"

        Example:
            ```python
            # Find all results excluded due to non-human subjects
            results = repo.get_by_exclusion_category(review_id, "Non-human subjects")
            ```
        """
        try:
            with self.session_factory.begin() as session:
                # Get all fields from ExclusionReasons model that end with _exclusion_reasons
                category_fields = [
                    field_name
                    for field_name in ExclusionReasons.model_fields.keys()
                    if field_name.endswith("_exclusion_reasons")
                ]

                # Build OR conditions to check each category array
                category_conditions = [
                    col(self.model_cls.exclusion_reason_categories)[field].op("@>")(
                        f'["{exclusion_reason}"]'
                    )
                    for field in category_fields
                ]

                query = (
                    select(self.model_cls)
                    .where(
                        and_(
                            self.model_cls.review_id == review_id,
                            or_(*category_conditions),
                        )
                    )
                    .options(selectinload(self.model_cls.pubmed_result))
                )
                return list(session.exec(query))
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch records by exclusion category for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_by_response_metadata(
        self,
        review_id: uuid.UUID,
        metadata: dict[str, JsonValue],
    ) -> list[ScreenAbstractResult]:
        """Get results by matching response_metadata JSONB fields.

        Example:
            ```python
            # Find all results from a specific model configuration
            results = repo.get_by_response_metadata(
                review_id, {"model": "gpt-4", "temperature": 0.0}
            )
            ```
        """
        try:
            with self.session_factory.begin() as session:
                query = select(self.model_cls).where(
                    self.model_cls.review_id == review_id,
                    *[
                        col(self.model_cls.response_metadata)[key] == value
                        for key, value in metadata.items()
                    ],
                )
                return list(session.exec(query))
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch records by response metadata for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc


class LogRepository(BaseRepository[LogRecord]):
    """Repository for log records."""

    def get_by_review_id(self, review_id: uuid.UUID) -> Sequence[LogRecord]:
        """Get log records by review ID."""
        try:
            with self.session_factory.begin() as session:
                query = select(self.model_cls).where(
                    self.model_cls.review_id == review_id
                )
                return list(
                    session.exec(query.options(selectinload(self.model_cls.review)))
                )
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch records by review ID for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc

    def get_by_level(
        self,
        level: LogLevel,
        review_id: uuid.UUID | None = None,
    ) -> Sequence[LogRecord]:
        """Get log records by level and optional review ID."""
        try:
            if review_id is None:
                with self.session_factory.begin() as session:
                    query = select(self.model_cls).where(
                        self.model_cls.level == level,
                    )
                    return list(session.exec(query))

            with self.session_factory.begin() as session:
                query = select(self.model_cls).where(
                    self.model_cls.review_id == review_id,
                    self.model_cls.level == level,
                )
                return list(
                    session.exec(query.options(selectinload(self.model_cls.review)))
                )
        except SQLAlchemyError as exc:
            msg = f"Failed to fetch records by review ID for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc


class ScreeningResolutionRepository(BaseRepository[ScreeningResolution]):
    """Repository for ScreeningResolution model operations.

    Handles saving and retrieving resolution decisions.
    """

    def get_by_pubmed_id(
        self, pubmed_result_id: uuid.UUID
    ) -> ScreeningResolution | None:
        """Get resolution by PubMedResult ID."""
        try:
            with self.session_factory.begin() as session:
                query = (
                    select(self.model_cls)
                    .where(self.model_cls.pubmed_result_id == pubmed_result_id)
                    .options(selectinload(self.model_cls.pubmed_result))
                )
                return session.exec(query).first()
        except SQLAlchemyError as exc:
            msg = f"Database error in get_by_pubmed_id for {self.model_cls.__name__}: {exc}"
            logger.exception(msg)
            raise RepositoryError(msg) from exc
