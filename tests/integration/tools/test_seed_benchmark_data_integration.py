import subprocess
import sys
import os
# import uuid # BENCHMARK_REVIEW_ID is a UUID, but imported from seed_benchmark_data

import pytest
# from pytest_mock import MockerFixture # Not used in this file directly anymore
from sqlmodel import Session, select
from sqlalchemy import text # Removed sqlalchemy_delete as _cleanup_db is removed
from loguru import logger

from sr_assistant.core import models
from tools.seed_benchmark_data import (
    BENCHMARK_EXCEL_PATH,
    BENCHMARK_REVIEW_ID,
    # parse_protocol_and_create_review, # Removed: No longer used
)

# Note: The db_session fixture is expected to be provided by tests/conftest.py
# and handle test DB connection and cleanup.
# The global clean_db fixture from conftest.py will handle setup/teardown.

@pytest.mark.integration
class TestSeedBenchmarkDataIntegration:
    def _run_seed_script(self) -> subprocess.CompletedProcess[str]:
        """Helper to run the seed_benchmark_data.py script."""
        # Ensure the script uses the same Python interpreter as the tests
        python_executable = sys.executable
        script_path = "tools/seed_benchmark_data.py"
        command = ["uv", "run", python_executable, script_path]
        
        # Get current environment and add/override ENVIRONMENT for the subprocess
        process_env = os.environ.copy()
        process_env["ENVIRONMENT"] = "test"
        
        result = subprocess.run(command, capture_output=True, text=True, check=False, env=process_env)
        if result.returncode != 0:
            print("stdout from script:", result.stdout)
            print("stderr from script:", result.stderr)
        return result

    # Removed local _cleanup_db and auto_cleanup_db fixture
    # Relying on global clean_db from conftest.py

    def test_seeding_script_creates_and_populates_data_correctly(self, db_session: Session):
        """
        Tests the full seeding process:
        1. Runs the seed_benchmark_data.py script.
        2. Verifies the SystematicReview is created in the DB.
        3. Verifies SearchResults are created and linked.
        4. Verifies data integrity for a sample.
        """
        # Query and print current enum values in the test DB
        try:
            enum_values_result = db_session.execute(text("SELECT unnest(enum_range(NULL::searchdatabasesource_enum)) AS enum_value;")) # pyright: ignore[reportDeprecated]
            live_enum_values = [row[0] for row in enum_values_result]
            print(f"\nLIVE ENUM VALUES in sra_integration_test for searchdatabasesource_enum: {live_enum_values}")
        except Exception as e:
            print(f"\nError querying enum values: {e!r}")
            live_enum_values = [] # Ensure it's defined

        # 1. Run the script
        script_result = self._run_seed_script()
        assert script_result.returncode == 0, f"Script failed: {script_result.stderr}"

        # 2. Verify SystematicReview
        # Fetch the review created by the script using explicit select
        stmt_review = select(models.SystematicReview).where(models.SystematicReview.id == BENCHMARK_REVIEW_ID)
        review_in_db = db_session.exec(stmt_review).one_or_none()
        assert review_in_db is not None, f"SystematicReview with ID {BENCHMARK_REVIEW_ID} not found in DB."

        # Define expected inclusion and exclusion criteria (as they actually appear in the script)
        expected_inclusion_criteria_str = """
  <InclusionCriteria>
    <Population>
      <Item>Homeless</Item>
      <Item>Key informants reporting on needs of Homeless</Item>
    </Population>
    <Setting>
      <Item>Data collected in Republic of Ireland</Item>
    </Setting>
    <StudyDesign>
      <Item>Empirical primary or secondary data on a health topic</Item>
      <Item>Quantitative studies</Item>
      <Item>Qualitative studies</Item>
    </StudyDesign>
    <PublicationType>
      <Item>Peer-reviewed publications</Item>
      <Item>Conference Abstracts</Item>
      <Item>Systematic reviews examined for individual studies meeting inclusion criteria</Item>
    </PublicationType>
    <Topic>
      <Item>Health conditions (e.g., addiction, diabetes, cancer, communicable/non-communicable disease, STI, pregnancy and childbirth, etc.)</Item>
      <Item>Health behaviours (e.g., nutrition, child development, tobacco use, vaccination, etc.)</Item>
      <Item>Health care access, utilisation, quality</Item>
      <Item>Social determinants of health (e.g., social and community context, education, economic stability)</Item>
    </Topic>
    <Language>English</Language>
    <Date>Published in 2012 or later</Date>
  </InclusionCriteria>"""

        expected_exclusion_criteria_str = """  <ExclusionCriteria>
    <Population></Population>
    <Setting>
      <Item>No data from the Republic of Ireland</Item>
      <Item>Studies using international/European datasets without specific outcomes for Republic of Ireland</Item>
    </Setting>
    <StudyDesign>
      <Item>No empirical primary or secondary data on a health topic</Item>
      <Item>Modelling studies</Item>
      <Item>Commentaries/Letters</Item>
      <Item>Individual case reports</Item>
    </StudyDesign>
    <PublicationType>
      <Item>Policy papers</Item>
      <Item>Guidelines</Item>
      <Item>Systematic reviews containing studies meeting inclusion criteria</Item>
      <Item>Grey literature (government documents and reports, pre-print articles, research reports, statistical reports)</Item>
    </PublicationType>
    <Topic>
      <Item>Animal study</Item>
      <Item>Economic/health care/housing policy not relating to health</Item>
    </Topic>
    <Language>Any language that is not English</Language>
    <Date>Published before 2012</Date>
  </ExclusionCriteria>"""
        
        expected_research_question = "Benchmark: What is the health status, healthcare access/utilization/quality, and what are the health conditions, health behaviours, and social determinants of health for individuals experiencing homelessness in the Republic of Ireland, and how do these compare to the general housed population where data allows?"

        assert review_in_db.id == BENCHMARK_REVIEW_ID # ID is fixed
        assert review_in_db.research_question == expected_research_question
        assert review_in_db.inclusion_criteria == expected_inclusion_criteria_str
        assert review_in_db.exclusion_criteria == expected_exclusion_criteria_str
        
        assert review_in_db.review_metadata is not None
        assert review_in_db.review_metadata.get("benchmark_source_protocol_version") == "Story 4.1 - Pre-defined PICO and Exclusion Criteria"
        assert review_in_db.review_metadata.get("benchmark_data_source_csv") == str(BENCHMARK_EXCEL_PATH)


        # 3. Verify SearchResults
        search_results_in_db_stmt = select(models.SearchResult).where(
            models.SearchResult.review_id == BENCHMARK_REVIEW_ID
        )
        search_results_in_db = db_session.exec(search_results_in_db_stmt).all()
        
        # Count check: Read the Excel to know how many results to expect
        # This is a bit redundant with the unit test for parse_excel, but good for integration.
        # For simplicity here, we'll hardcode the expected count based on the current Excel.
        # A more robust way would be to parse the Excel here too, or rely on the script output if it logged it.
        # From current benchmark_human_ground_truth.xlsx: 585 entries total (valid rows with non-NaN keys)
        # 365 excluded (N) + 220 included (Y) + 1 anomalous (220) = 586 total, but 585 valid rows
        expected_search_result_count = 585 # Updated from 586, actual valid row count with non-NaN keys
        assert len(search_results_in_db) == expected_search_result_count, \
            f"Expected {expected_search_result_count} search results, found {len(search_results_in_db)}"

        # Diagnostic: Check if the specific source_id is in the database
        all_source_ids_in_db = {res.source_id for res in search_results_in_db}
        if "pmid_33882220" not in all_source_ids_in_db:
            logger.warning("DIAGNOSTIC: pmid_33882220 NOT FOUND IN DB source_ids")
            # Optionally print a few source_ids to see what is there
            logger.debug(f"First 10 source_ids in DB: {list(all_source_ids_in_db)[:10]}")
        else:
            logger.info("DIAGNOSTIC: pmid_33882220 FOUND IN DB source_ids")

        # 4. Verify data integrity for a sample
        # Let's check a specific known entry from the Excel.
        # Using the first data row from the current Excel: rayyan-388371190
        sample_key_to_check = "rayyan-388371190"
        sample_result_stmt = select(models.SearchResult).where(
            models.SearchResult.review_id == BENCHMARK_REVIEW_ID,
            models.SearchResult.source_id == sample_key_to_check
        )
        sample_result = db_session.exec(sample_result_stmt).one_or_none()
        assert sample_result is not None, f"SearchResult with source_id {sample_key_to_check} not found."
        
        assert sample_result.title == "CONFERENCE SPECIAL 2021 LEADING THE WAY" # From Excel
        assert sample_result.authors == [] # Authors field is blank in Excel for this row
        assert sample_result.year == "2022" # From Excel
        assert sample_result.source_db == models.SearchDatabaseSource.OTHER # Inferred by script
        # Benchmark decision for rayyan-388371190: check "Included after T&A screen" column value
        assert sample_result.source_metadata["benchmark_human_decision"] is False 
        assert sample_result.source_metadata["original_key"] == sample_key_to_check
        assert sample_result.source_metadata["included_after_ta_screen"] == "N" # From Excel


    def test_seeding_script_is_idempotent_on_rerun(self, db_session: Session):
        """
        Tests that running the script multiple times doesn't duplicate data
        or cause errors, and the final state is correct.
        """
        # Run 1
        script_result1 = self._run_seed_script()
        assert script_result1.returncode == 0, f"Script failed on first run: {script_result1.stderr}"

        # Check count after run 1
        search_results_in_db_stmt_run1 = select(models.SearchResult).where(
            models.SearchResult.review_id == BENCHMARK_REVIEW_ID
        )
        count_after_run1 = len(db_session.exec(search_results_in_db_stmt_run1).all())
        expected_search_result_count = 585 # Updated from 586, actual valid row count with non-NaN keys
        assert count_after_run1 == expected_search_result_count

        # Run 2
        script_result2 = self._run_seed_script()
        assert script_result2.returncode == 0, f"Script failed on second run: {script_result2.stderr}"

        # Verify SystematicReview still exists and is correct (basic check) using explicit select
        stmt_review_run2 = select(models.SystematicReview).where(models.SystematicReview.id == BENCHMARK_REVIEW_ID)
        review_in_db_run2 = db_session.exec(stmt_review_run2).one_or_none()
        assert review_in_db_run2 is not None
        
        # Verify SearchResults count is still the same
        search_results_in_db_stmt_run2 = select(models.SearchResult).where(
            models.SearchResult.review_id == BENCHMARK_REVIEW_ID
        )
        count_after_run2 = len(db_session.exec(search_results_in_db_stmt_run2).all())
        assert count_after_run2 == expected_search_result_count, \
            "Search result count changed after re-running the script."

        # Optionally, do a more thorough data verification like in the first test
        # to ensure the data was correctly overwritten/updated, not just count-matched.
        # For now, count check is a good indicator of idempotency.
        sample_key_to_check_rerun = "rayyan-388371190" # Use the same key as the other test
        sample_result_stmt_rerun = select(models.SearchResult).where(
            models.SearchResult.review_id == BENCHMARK_REVIEW_ID,
            models.SearchResult.source_id == sample_key_to_check_rerun
        )
        sample_result_run2 = db_session.exec(sample_result_stmt_rerun).one_or_none()
        assert sample_result_run2 is not None
        assert sample_result_run2.title == "CONFERENCE SPECIAL 2021 LEADING THE WAY" # From Excel
        assert sample_result_run2.source_metadata["benchmark_human_decision"] is False # From Excel "N" value


    def test_seeding_script_handles_missing_excel_gracefully(self, db_session: Session):
        """
        Tests that if the benchmark Excel is missing, the script reports an error
        and doesn't seed SearchResults (and potentially cleans up or doesn't create the Review).
        The current script behavior is to log an error and exit if Excel parsing fails.
        The review *might* be created before Excel parsing is attempted.
        """
        original_excel_path = BENCHMARK_EXCEL_PATH
        
        # Mock BENCHMARK_EXCEL_PATH in the tools.seed_benchmark_data module
        # to point to a non-existent file for the script's execution context.
        # This is tricky because the script is run as a subprocess.
        # Modifying it here won't affect the subprocess directly unless the script
        # reads it from an env var that we can set, or we modify the script file itself.
        
        # Alternative: Temporarily rename the Excel, run script, then rename back.
        temp_missing_excel_path = original_excel_path.with_suffix(".excel.temp_missing")
        
        renamed = False
        try:
            if original_excel_path.exists():
                original_excel_path.rename(temp_missing_excel_path)
                renamed = True
            
            script_result = self._run_seed_script()
            
            # Script should fail or indicate failure if Excel is critical.
            # The script currently logs an error and continues, creating the review but no search results.
            # Let's assert that it completes (returncode 0 if it doesn't sys.exit)
            # and no search results are created for the benchmark review.
            # The script *will* create/update the review protocol.
            
            assert script_result.returncode == 0 # Script completes even if Excel parsing fails

            # Verify review might exist (or was touched) using explicit select
            stmt_review_missing_excel = select(models.SystematicReview).where(models.SystematicReview.id == BENCHMARK_REVIEW_ID)
            review_in_db = db_session.exec(stmt_review_missing_excel).one_or_none()
            assert review_in_db is not None # Review protocol is independent of Excel

            # Verify no SearchResults were created for this review
            search_results_in_db_stmt = select(models.SearchResult).where(
                models.SearchResult.review_id == BENCHMARK_REVIEW_ID
            )
            search_results_in_db = db_session.exec(search_results_in_db_stmt).all()
            assert len(search_results_in_db) == 0, \
                "SearchResults were created even when Excel was expected to be missing."
            
            assert "Benchmark Excel file not found" in script_result.stdout or \
                   "Benchmark Excel file not found" in script_result.stderr, \
                   "Script should log an error about missing Excel."

        finally:
            if renamed and temp_missing_excel_path.exists():
                temp_missing_excel_path.rename(original_excel_path)

    # Add more tests as needed, e.g., for partial failures, specific data validation scenarios. 