# tests/integration/core/test_repositories.py
from loguru import logger
from sqlmodel import Session

from sr_assistant.core.repositories import SystematicReviewRepository
from tests.integration.data.test_data import REVIEW_1_ID


def test_relationship_loading_behavior(db_session: Session) -> None:
    """Determine actual relationship loading behavior."""
    repo = SystematicReviewRepository()

    logger.info("Testing get_by_id...")
    review = repo.get_by_id(REVIEW_1_ID)
    assert review is not None

    logger.info("Checking if relationship access triggers loads...")
    if hasattr(review, "pubmed_results"):
        logger.info("Has {} PubMed results", len(review.pubmed_results))

    logger.info("Testing get_with_pubmed_results...")
    review_with_results = repo.get_with_pubmed_results(REVIEW_1_ID)
    assert review_with_results is not None
    assert len(review_with_results.pubmed_results) > 0
    logger.info("Has {} PubMed results", len(review_with_results.pubmed_results))

    logger.info("Testing get_with_all...")
    review_all = repo.get_with_all(REVIEW_1_ID)
    assert review_all is not None
    assert len(review_all.pubmed_results) > 0
    assert len(review_all.screen_abstract_results) > 0
    assert len(review_all.log_records) > 0

def test_get_with_pubmed_results(db_session: Session) -> None:
    """Test the explicit PubMed results loading method."""
    repo = SystematicReviewRepository()
    review = repo.get_with_pubmed_results(REVIEW_1_ID)
    assert review is not None
    assert len(review.pubmed_results) > 0

    for result in review.pubmed_results:
        logger.info("PubMed result: {} - {}", result.id, result.title)
        if result.conservative_result:
            logger.info("  Conservative: {}", result.conservative_result.decision)
        if result.comprehensive_result:
            logger.info("  Comprehensive: {}", result.comprehensive_result.decision)

def test_get_with_all_relationships(db_session: Session) -> None:
    """Test loading all relationships."""
    repo = SystematicReviewRepository()
    review = repo.get_with_all(REVIEW_1_ID)
    assert review is not None

    # All relationships should be loaded
    assert len(review.pubmed_results) > 0
    assert len(review.screen_abstract_results) > 0
    assert len(review.log_records) > 0

    logger.info("Review: {}", review.id)
    logger.info("PubMed results: {}", len(review.pubmed_results))
    logger.info("Screening results: {}", len(review.screen_abstract_results))
    logger.info("Log records: {}", len(review.log_records))
