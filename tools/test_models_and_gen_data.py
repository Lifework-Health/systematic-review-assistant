"""Generate test data for systematic review database using SQLModel."""

import os
from datetime import UTC, datetime
import uuid
import argparse

from sqlmodel import Session, SQLModel, create_engine, select, col
import sqlalchemy as sa
from dotenv import load_dotenv

from sr_assistant.core.models import (
    SystematicReview,
    PubMedResult,
    ScreenAbstractResult,
)
from sr_assistant.core.types import (
    ScreeningDecisionType,
    ScreeningStrategyType
)
# from sr_assistant.core.schemas import ExclusionReasons

cleanup_flag = False

def confirm_database_drop(engine: sa.Engine) -> bool:
    """Confirm database drop with user."""
    url = engine.url
    print(f"\nWARNING: About to drop all tables in database:")
    print(f"Database: {url.database}")
    print(f"Host: {url.host}")
    print(f"User: {url.username}")

    while True:
        response = input("\nDo you want to proceed? [y/N] ").lower().strip()
        if response in {'y', 'yes'}:
            return True
        if response in {'n', 'no', ''}:  # Empty response counts as no
            return False
        print("Please answer 'y' or 'n'")

def cleanup_database(engine: sa.Engine, cleanup: bool = False) -> None:
    """Drop all tables and custom types from the database.

    SQLmodel/SA doesn't seem to drop `sa.ENUM` types contrary to documentation, so we
    just drop the ``public`` schema altogether.

    Args:
        engine (sa.Engine): SQLAlchemy engine to use for database operations.
        cleanup (bool, optional): If True, drop and re-create 'public' schema. Defaults
            to False which is a no-op.
    """
    print(f"Dropping public schema with engine {engine!r}")
    if not cleanup:
        print("ERROR: cleanup_database called with cleanup=False, aborting")
        return

    with engine.connect() as conn:
        conn.execute(sa.text("""
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO postgres;
            GRANT ALL ON SCHEMA public TO public;
        """))
        conn.commit()
        # SQLModel.metadata.drop_all(engine) # Not strictly needed after schema drop

def create_test_data(engine: sa.Engine) -> None:
    """Create test data in database.

    Creates reviews, PubMed results, and screening results with proper relationships.
    Uses SQLModel for clean, type-safe database operations.
    """

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create reviews
        reviews = [
            SystematicReview(
                id=uuid.uuid4(),
                background="Test background for systematic review on cancer treatment",
                research_question="What is the efficacy of immunotherapy in treating melanoma?",
                inclusion_criteria="RCTs studying immunotherapy in melanoma patients",
                exclusion_criteria="Non-RCT studies, non-melanoma cancers",
            ),
            SystematicReview(
                id=uuid.uuid4(),
                background="COVID-19 vaccine effectiveness study",
                research_question="How effective are mRNA vaccines against COVID-19 variants?",
                inclusion_criteria="Clinical trials of mRNA vaccines",
                exclusion_criteria="Non-clinical studies, non-mRNA vaccines",
            ),
        ]
        # Add and commit reviews
        session.add_all(reviews)
        session.commit()

        # Create PubMed results for each review
        pubmed_results = []
        for review in reviews:
            for i in range(5):
                result = PubMedResult(
                    id=uuid.uuid4(),
                    review_id=review.id,
                    query=f"Test query for {review.research_question}",
                    pmid=f"PMD{i+1}",
                    pmc=f"PMC00{i+1}",
                    doi=f"10.1000/test.{i+1}",
                    title=f"Test Article {i+1} for Review {review.id}",
                    abstract=f"This is a test abstract for article {i+1}",
                    journal=f"Test Journal {i+1}",
                    year=str(2020 + i),
                )
                pubmed_results.append(result)

        # Add and commit PubMed results
        session.add_all(pubmed_results)
        session.commit()

        # Create screening results for each PubMed result
        screening_results = []
        screening_pairs = []  # Store pairs for later FK update
        for result in pubmed_results:
            trace_id = uuid.uuid4()

            # Conservative screening
            conservative = ScreenAbstractResult(
                id=uuid.uuid4(),
                review_id=result.review_id,
                pubmed_result_id=result.id,
                trace_id=trace_id,
                decision=ScreeningDecisionType.INCLUDE if result.year > "2022" else ScreeningDecisionType.EXCLUDE,
                confidence_score=0.85,
                rationale="Test rationale for conservative screening",
                extracted_quotes=["Test quote 1", "Test quote 2"],
                exclusion_reason_categories={},  # Empty dict for testing
                screening_strategy=ScreeningStrategyType.CONSERVATIVE,
                model_name="test-model",
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                response_metadata={"test": "metadata"},
            )
            screening_results.append(conservative)

            # Comprehensive screening - Introduce conflict for odd indices
            comp_decision = (
                ScreeningDecisionType.EXCLUDE
                if result.year > "2022" and int(result.year) % 2 != 0 # Conflict on odd year if conservative included
                else ScreeningDecisionType.INCLUDE
            )
            comprehensive = ScreenAbstractResult(
                id=uuid.uuid4(),
                review_id=result.review_id,
                pubmed_result_id=result.id,
                trace_id=trace_id,
                decision=comp_decision,
                confidence_score=0.75,
                rationale="Test rationale for comprehensive screening",
                extracted_quotes=["Test quote 3", "Test quote 4"],
                exclusion_reason_categories={},  # Empty dict for testing
                screening_strategy=ScreeningStrategyType.COMPREHENSIVE,
                model_name="test-model",
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC),
                response_metadata={"test": "metadata"},
            )
            screening_results.append(comprehensive)

            screening_pairs.append((result, conservative.id, comprehensive.id))

        # Add screening results first
        session.add_all(screening_results)
        session.commit()

        # Now update PubMed results with the committed screening result IDs
        for result, cons_id, comp_id in screening_pairs:
            result.conservative_result_id = cons_id
            result.comprehensive_result_id = comp_id
        session.commit()

        # Verify results using SQLModel select
        stmt = select(ScreenAbstractResult).order_by(col(ScreenAbstractResult.created_at))
        db_results = session.exec(stmt).all()
        print(f"Created {len(db_results)} screening results")
        for result in db_results:
            print(f"- {result.created_at} {result.screening_strategy}: {result.decision} ({result.confidence_score})")

if __name__ == "__main__":
    load_dotenv(".env.test", override=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true", help="Drop all tables and enum types before creating test data")
    args = parser.parse_args()

    # Set the global flag based on the argument
    cleanup_flag = args.cleanup

    db_url = os.getenv("SRA_DATABASE_URL", os.getenv("DATABASE_URL", ""))
    if "sra_integration_test" not in db_url:
        print("Error: (SRA_)|DATABASE_URL must be set to integration test database")
        exit(1)

    engine = create_engine(db_url, echo=True)

    # Call the local cleanup_database function
    if cleanup_flag:
        # Confirmation happens interactively if needed
        if confirm_database_drop(engine=engine):
            print("Running in cleanup mode")
            cleanup_database(engine, cleanup=True)
        else:
            print("Cleanup cancelled by user.")
            exit(0)
    else:
        print("Running in non-cleanup mode")

    create_test_data(engine)
