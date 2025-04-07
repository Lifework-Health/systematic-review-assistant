# tests/integration/conftest.py
import uuid
from datetime import datetime, timezone

# Fixed UUIDs for test data
REVIEW_1_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
REVIEW_2_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
PUBMED_1_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
PUBMED_2_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
SCREEN_CONS_1_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
SCREEN_COMP_1_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")

# Fixed timestamp for tests
FIXED_DATETIME = datetime(2025, 1, 1, tzinfo=timezone.utc)

# Test data with known values
REVIEW_1_DATA = {
    "id": REVIEW_1_ID,
    "background": "Test background for cancer treatment",
    "research_question": "What is the efficacy of immunotherapy?",
    "inclusion_criteria": "RCTs studying immunotherapy",
    "exclusion_criteria": "Non-RCT studies",
}

PUBMED_1_DATA = {
    "id": PUBMED_1_ID,
    "review_id": REVIEW_1_ID,
    "query": "immunotherapy cancer RCT",
    "pmid": "12345",
    "pmc": "PMC12345",
    "doi": "10.1000/test.1",
    "title": "Test Article 1",
    "abstract": "This is test abstract 1",
    "journal": "Test Journal",
    "year": "2023",
}
