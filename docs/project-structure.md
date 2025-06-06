# MPH SR Prototype Project Structure

## Overview

The project is organized to promote a clear separation of concerns, enabling easier maintenance, testing, and development, particularly with AI agents in mind. The structure distinguishes between core domain logic, application-specific components (including UI and LLM agents), and infrastructure concerns like database interactions and external service integrations. The `src/sr_assistant/` directory houses the main Python application code. This modular approach is intended to make it straightforward for AI agents to locate, understand, and modify specific parts of the codebase.

## Top-Level Directory Structure

- **`src/sr_assistant/`**: Main application source code.
    - **`app/`**: Houses application-specific logic, Streamlit UI components, main application setup, and LLM agent orchestrations.
        - **`agents/`**: Contains modules defining LangChain/LangGraph agents (e.g., `ScreeningAgents`, `ResolverAgent`), their prompts, Pydantic schemas for inputs/outputs, and related orchestration logic.
        - **`pages/`**: Streamlit page modules (e.g., `search.py`, `screen_abstracts.py`, `protocol.py`). Each file typically defines a distinct page or view in the UI.
        - **`services/`**: Contains the `SearchService` and potentially other application-level services that orchestrate business logic, interact with repositories, and manage external API calls (like PubMed). Currently, this includes `services.py`.
        - **`utils/`**: Common utility functions and helpers specific to the Streamlit application or UI layer (e.g., `app/utils.py`).
        - **`config.py`**: Application configuration management (e.g., loading environment variables, Pydantic settings models).
        - **`database.py`**: Database session management and engine setup.
        - **`logging.py`**: Logging configuration for the application (Loguru, LogFire).
        - **`main.py`**: Main entry point for the Streamlit application.
        - `pubmed_integration.py`: (Under Review) Contains PubMed specific parsing. Functionality may be merged into `SearchService` or refactored.
        - `__init__.py`
    - **`core/`**: Core business logic, domain models (SQLModel), Pydantic schemas for data validation, and repository implementations.
        - **`models.py`**: SQLModel definitions for database tables (e.g., `Review`, `SearchResult`, `ScreeningResolution`).
        - **`repositories.py`**: Contains repository classes (e.g., `SearchResultRepository`, `ScreeningResolutionRepository`) responsible for data access logic, interacting directly with the database.
        - **`schemas.py`**: Pydantic schemas used for data validation, API request/response models (if any non-UI APIs were to be built), and structuring data for LLM agents.
        - **`types.py`**: Custom data types, Enums (e.g., `ScreeningDecision`, `SearchDatabaseSource`).
        - **`constants.py`**: Project-wide constants.
        - `repositories_old.py`: (To be removed) Legacy repository implementations.
        - `__init__.py`
    - `step1/`: (To be removed) Legacy code related to initial suggestion agent.
    - `step2/`: (To be removed) Legacy code related to earlier search and screening implementation.
    - `__init__.py`
- **`tests/`**: Contains all tests.
    - **`unit/`**: Unit tests for individual functions, classes, and modules, isolated from external dependencies. Organized to mirror the `src/sr_assistant/` structure (e.g., `tests/unit/app/`, `tests/unit/core/`).
    - **`integration/`**: Integration tests that verify interactions between different components (e.g., service and repository, agent and external API). These tests may require a database connection (e.g., to `sra_integration_test`) or mock external services.
    - **`e2e/`**: (Future) End-to-end tests, simulating full user workflows through the Streamlit UI. Currently minimal or placeholder.
    - **`st/`**: (Contains Streamlit-specific concurrency tests) These might be reorganized or integrated into `e2e/` or `integration/` as appropriate if they test application functionality rather than just Streamlit behavior.
    - **`conftest.py`**: Pytest fixtures, hooks, and configuration shared across tests (e.g., database setup/teardown for integration tests).
    - `__init__.py`
- **`alembic/`**: Database migration scripts managed by Alembic.
    - **`versions/`**: Individual, versioned migration files generated by Alembic.
    - **`env.py`**: Alembic environment configuration, defines how migrations are run.
    - `script.py.mako`: Template for new migration scripts.
- **`docs/`**: Project documentation.
    - **`templates/`**: Contains markdown templates for various documents (PRD, architecture, etc.).
    - Other markdown files for PRDs (`prd-recovery.md`, `prd-resolver.md`), project briefs, etc., with Epic files organized in `docs/epics/` directory.
- **`tools/`**: Helper scripts for development, data generation, or one-off tasks (e.g., `test_models_and_gen_data.py`, `supabase-fn-new.py`).
- **`supabase/`**: Supabase specific configurations, edge functions (if any are actively used beyond database hosting).
    - **`functions/`**: Directory for Supabase Edge Functions.
- **`.github/`**: GitHub specific files.
    - **`workflows/`**: CI/CD pipeline definitions using GitHub Actions (e.g., running tests on PRs).
- **`pyproject.toml`**: Project metadata, dependencies (managed by `uv`), and tool configurations (Ruff, Pyright, Pytest, etc.).
- **`uv.lock`**: Lock file for Python dependencies, managed by `uv`. This file ensures reproducible builds by locking dependency versions.
- **`Makefile`**: Defines tasks for common development operations (e.g., `make lint`, `make test`, `make run`).
- **`.env.example`**: Example environment variable file for base configuration.
- **`.env.local.example`**: Example for local overrides.
- **`.env.test.example`**: Example for test environment configuration.
- **`README.md`**: Project overview, setup instructions, and contribution guidelines.
- **`LICENSE`**: Project license file (e.g., MIT, Apache 2.0).
- **`.gitignore`**: Specifies intentionally untracked files that Git should ignore.
- **`alembic.ini`**: Configuration file for Alembic.
- **`.markdownlint.yaml`**: Configuration for markdown linting.
- **`.pre-commit-config.yaml`**: Configuration for pre-commit hooks (currently disabled, to be re-enabled post-recovery).
- **`CHANGELOG.md`**: Log of changes for each version/release.

**Key Removals/Changes noted based on your feedback:**

- Emphasis on `src/sr_assistant/app/services/` (currently `services.py` directly in `app/`) for service layer components.
- `src/sr_assistant/app/pubmed_integration.py` is under review for refactoring/merging.

## Change Log

| Change        | Date       | Version | Description   | Author          |
| ------------- | ---------- | ------- | ------------- | --------------- |
| Initial draft | 2025-05-09 | 0.1     | Initial draft | Architect Agent |
| ...           | ...        | ...     | ...           | ...             |
