"""Pytest fixtures for integration testing."""

import os
from collections.abc import Generator
from typing import Any

import pytest
import sqlalchemy as sa
from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

# Remove sys.path modification

# Remove incorrect import


@pytest.fixture(scope="session")
def db_engine() -> Generator[sa.Engine, None, None]:
    """Yields a SQLAlchemy engine scoped to the test session."""
    load_dotenv(".env.test", override=True)
    db_url = os.getenv("SRA_DATABASE_URL", os.getenv("DATABASE_URL", ""))

    if not db_url:
        pytest.fail("DATABASE_URL or SRA_DATABASE_URL not set in environment/.env.test")

    if "sra_integration_test" not in db_url:
        pytest.fail(
            f"DATABASE_URL '{db_url}' does not seem to be the integration test DB ('sra_integration_test')"
        )

    print(f"\nCreating session engine for: {db_url}")
    engine = create_engine(db_url, echo=False)
    yield engine
    print("\nDisposing session engine.")
    engine.dispose()


@pytest.fixture(scope="function", autouse=True)
def clean_db(db_engine: sa.Engine, request: pytest.FixtureRequest):
    """Cleans (drops/recreates public schema) and recreates tables before each integration test."""
    marker = request.node.get_closest_marker("integration")
    if marker is None:
        yield
        return

    print("\nRunning DB cleanup for integration test...")
    # Drop and recreate public schema directly
    with db_engine.connect() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE;"))
        conn.execute(sa.text("CREATE SCHEMA public;"))
        # Grant permissions if necessary for your test user/role
        conn.execute(sa.text("GRANT ALL ON SCHEMA public TO postgres;"))
        conn.execute(sa.text("GRANT ALL ON SCHEMA public TO public;"))
        conn.commit()
    print("Public schema dropped and recreated.")

    # Recreate tables
    print("Recreating all tables...")
    SQLModel.metadata.create_all(db_engine)
    print("Table recreation complete.")
    yield  # Test runs here
    print("DB cleanup fixture finished.")


@pytest.fixture(scope="function")
def db_session(db_engine: sa.Engine, clean_db: Any) -> Generator[Session, None, None]:
    """Yields a DB session with transaction management for a test function."""
    with Session(db_engine) as session:
        print("\nYielding DB session for test...")
        try:
            yield session
        finally:
            print("Closing DB session after test.")
