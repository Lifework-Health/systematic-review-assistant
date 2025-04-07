from __future__ import annotations

import uuid

import streamlit as st
from Bio import Entrez
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger
from pydantic import BaseModel, Field

<<<<<<< HEAD
from sr_assistant.core.repositories import PubMedResultRepository, ScopusRepository
from sr_assistant.step2.pubmed_integration import pubmed_fetch_details, pubmed_search


def build_scopus_query(components: dict) -> str:
    """Build Scopus query from components."""
    query_parts = []
    
    # Title/Abstract/Keywords
    if components.get('keywords'):
        query_parts.append(f"TITLE-ABS-KEY({components['keywords']})")
    
    # Publication Year
    if components.get('year_from') or components.get('year_to'):
        year_from = components.get('year_from', '1900')
        year_to = components.get('year_to', '2024')
        query_parts.append(f"PUBYEAR BET {year_from} AND {year_to}")
    
    # Document Type
    if components.get('doc_type'):
        query_parts.append(f"DOCTYPE({components['doc_type']})")
    
    # Language
    if components.get('language'):
        query_parts.append(f"LANGUAGE({components['language']})")
        
    return " AND ".join(query_parts)


def search_page(review_id: UUID | None = None) -> None:
    """Literature search page."""
    if not review_id:
        st.error("Please select a review protocol first")
        st.stop()

    pubmed_repo = PubMedResultRepository()
    scopus_repo = ScopusRepository(st.secrets["SCOPUS_API_KEY"])

    st.header("Literature Search")
    
    # Database selector
    database = st.selectbox(
        "Select Database",
        ["PubMed", "Scopus"]
    )

    with st.form("search_form"):
        if database == "Scopus":
            # Scopus Advanced Search Builder
            st.subheader("Scopus Search Builder")
            
            col1, col2 = st.columns(2)
            with col1:
                keywords = st.text_area("Keywords/Phrases", 
                    help="Enter search terms. Will be searched in title, abstract, and keywords.")
                doc_type = st.multiselect("Document Type",
                    ["ar", "re", "cp", "ch"],
                    default=["ar"],
                    help="ar=Article, re=Review, cp=Conference Paper, ch=Chapter")
                
            with col2:
                year_from = st.number_input("Year From", min_value=1900, max_value=2024)
                year_to = st.number_input("Year To", min_value=1900, max_value=2024, value=2024)
                language = st.selectbox("Language", ["eng", "all"], help="Filter by language")

            # Build query
            query_components = {
                "keywords": keywords,
                "year_from": year_from,
                "year_to": year_to,
                "doc_type": ",".join(doc_type),
                "language": language if language != "all" else None
            }
            
            search_query = build_scopus_query(query_components)
            st.code(search_query, language="text")
            
            st.info("""
            Scopus Search Tips:
            - Use quotation marks for exact phrases: "machine learning"
            - Use W/n for proximity: "heart" W/3 "attack" finds terms within 3 words
            - Use PRE/n for ordered proximity: "heart" PRE/3 "disease"
            - Use * for wildcards: therap* finds therapy, therapeutic, etc.
            """)

        else:
            # PubMed search
            search_query = st.text_area(
                "PubMed Query",
                help="Enter PubMed search terms. Use MeSH terms and PubMed syntax."
            )
            max_results = st.number_input("Max Results", value=500, min_value=1)
            
            st.info("""
            PubMed Search Tips:
            - Use [MeSH] for Medical Subject Headings
            - Use quotation marks for exact phrases
            - Use AND, OR, NOT for boolean operators
            - Use filters like: AND Clinical Trial[Publication Type]
            """)

        submitted = st.form_submit_button("Search")
=======
from sr_assistant.core.models import CriteriaFramework, SystematicReview
from sr_assistant.core.repositories import (
    PubMedResultRepository,
    SystematicReviewRepository,
)
from sr_assistant.step2.pubmed_integration import pubmed_fetch_details, pubmed_search


class PubMedQuery(BaseModel):
    """PubMed query based on review protocol."""

    query: str = Field(
        ...,
        title="PubMed Query",
        description="PubMed query tailored to the review protocol, using PICO elements.",
    )


query_context = """\
Given the following review protocol, generate a valid PubMed query suitable for an initial search in PubMed. Use PubMed's field tags (like [tiab], [mh], [pt]) and boolean operators (AND, OR, NOT) effectively. Combine the PICO elements logically.

Background:
{background}

Research question:
{research_question}

PICO Criteria:
Population: {population}
Intervention: {intervention}
Comparison: {comparison}
Outcome: {outcome}

Explicit Exclusion Criteria (apply using NOT if appropriate):
{exclusion_criteria}"""

query_draft_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert systematic review PubMed search query builder. Given the PICO-based protocol below, generate an effective PubMed query.",
        ),
        ("user", query_context),
    ]
)


def init_query_chain():
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0).with_structured_output(
        PubMedQuery
    )
    chain = query_draft_prompt | llm
    st.session_state.query_chain = chain


def get_query(review: SystematicReview) -> str:
    """Generates a PubMed query string based on the review's PICO criteria."""
    if (
        review.criteria_framework != CriteriaFramework.PICO
        or not review.criteria_framework_answers
    ):
        logger.warning(
            "Review criteria framework is not PICO or answers are missing. Falling back to basic query gen."
        )
        fallback_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Generate a basic PubMed query based on the research question.",
                ),
                ("user", "Research Question: {research_question}"),
            ]
        )
        fallback_chain = fallback_prompt | ChatOpenAI(
            model="gpt-4o", temperature=0.0
        ).with_structured_output(PubMedQuery)
        result_object: PubMedQuery = fallback_chain.invoke(
            {"research_question": review.research_question}
        )
        return result_object.query if result_object else ""

    pico = review.criteria_framework_answers
    logger.info(f"Generating query from PICO: {pico}")
    result_object: PubMedQuery = st.session_state.query_chain.invoke(
        {
            "background": review.background or "",
            "research_question": review.research_question,
            "population": pico.get("population", ""),
            "intervention": pico.get("intervention", ""),
            "comparison": pico.get("comparison", ""),
            "outcome": pico.get("outcome", ""),
            "exclusion_criteria": review.exclusion_criteria or "",
        }
    )
    return result_object.query if result_object else ""


def gen_query_cb() -> None:
    st.session_state.query_value = get_query(st.session_state.review)


def expand_query_cb() -> None:
    Entrez.email = st.session_state.config.NCBI_EMAIL
    Entrez.api_key = st.session_state.config.NCBI_API_KEY.get_secret_value()

    with Entrez.esearch(db="pubmed", term=st.session_state.query_value) as handle:
        result = Entrez.read(handle)  # type: ignore
        res = result.get("QueryTranslation", "")  # type: ignore
    st.session_state.query_value = res


def init_review_repository() -> SystematicReviewRepository:
    if "repo_review" not in st.session_state:
        repo = SystematicReviewRepository()
        st.session_state.repo_review = repo
    return st.session_state.repo_review


def init_pubmed_repository() -> PubMedResultRepository:
    if "repo_pubmed" not in st.session_state:
        repo = PubMedResultRepository()
        st.session_state.repo_pubmed = repo
    return st.session_state.repo_pubmed


def search_page(review_id: uuid.UUID | None = None) -> None:
    """PubMed search page."""
    st.title("PubMed Search")
    st.markdown(
        "This page allows you to search PubMed for relevant articles based on your systematic review protocol."
    )
    init_review_repository()
    if (
        not review_id
        or "review_id" not in st.session_state
        or st.session_state.review_id != review_id
    ):
        # Added check if the review_id in session matches the one passed (or expected)
        st.error(
            "Invalid or missing review context. Please go back to the protocol page."
        )
        st.stop()

    if "review" not in st.session_state or st.session_state.review.id != review_id:
        review = st.session_state.repo_review.get_by_id(review_id)
        if not review:
            st.error(f"Could not load review with ID: {review_id}")
            st.stop()
        st.session_state.review = review
    # Ensure the loaded review is used
    current_review = st.session_state.review

    init_query_chain()
    repo = init_pubmed_repository()

    # Initial query generation using the loaded review
    if "query_value" not in st.session_state or st.session_state.query_value is None:
        with st.spinner("Generating initial query based on PICO..."):
            st.session_state.query_value = get_query(current_review)  # Pass the review

    st.session_state.query_value = st.text_area(
        "Accept or modify PubMed Query",
        value=st.session_state.query_value,
        height=100,
        key="query",  # Keep key if needed for direct access, though callbacks use query_value
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        submitted = st.button("Search")
    with col2:
        st.session_state.max_results = st.slider(
            "Max results",
            min_value=1,
            max_value=500,
            value=50,
            step=5,
        )
    with col3:
        st.button("Generate query", on_click=gen_query_cb)
    with col4:
        st.button("Expand query", on_click=expand_query_cb)
>>>>>>> 51577862cfec852c9be7f2326673108c705badc3

    if submitted:
        with st.status("Searching...", expanded=True) as status:
            try:
<<<<<<< HEAD
                if database == "PubMed":
                    # PubMed search
                    pmids = pubmed_search(search_query, max_results)
                    if not pmids:
                        st.warning("No results found")
                        return
=======
                # Search PubMed
                logger.info("Searching PubMed: {!r}", st.session_state.query_value)
                st.write("Searching PubMed...")
                pmids = pubmed_search(
                    st.session_state.query_value, st.session_state.max_results
                )
                if not pmids:
                    st.warning("No results found")
                    status.update(
                        label="No results found", state="complete"
                    )  # Update status
                    st.stop()  # Stop further processing
>>>>>>> 51577862cfec852c9be7f2326673108c705badc3

                    records = pubmed_fetch_details(pmids)
                    results = pubmed_repo.store_results(review_id, search_query, records)
                    st.success(f"Found {len(results)} articles in PubMed")
                    
                else:
                    # Scopus search
                    results = scopus_repo.search(search_query, review_id)
                    st.success(f"Found {len(results)} articles in Scopus")

<<<<<<< HEAD
=======
                # Fetch details
                records = pubmed_fetch_details(pmids)
                logger.info(f"Fetched {len(records['PubmedArticle'])} study details")
                st.write(f"Fetched {len(records['PubmedArticle'])} study details")

                # Store in Supabase
                results = repo.store_results(
                    review_id, st.session_state.query_value, records
                )
                logger.info(f"Stored {len(results)} articles")
                st.success(f"Stored {len(results)} articles")
>>>>>>> 51577862cfec852c9be7f2326673108c705badc3
                status.update(label="Search complete", state="complete")
                
                # Store results in session state
                if database == "PubMed":
                    st.session_state.pubmed_results = results
                else:
                    st.session_state.scopus_results = results

            except Exception as e:
                logger.exception("Search failed")
                status.update(label="Search failed", state="error")
                st.error(str(e))
<<<<<<< HEAD
                logger.exception("Search failed")
                return

    # Show existing results
    st.divider()
    st.subheader("Search Results")
    
    tab1, tab2 = st.tabs(["PubMed Results", "Scopus Results"])
    
    with tab1:
        pubmed_results = pubmed_repo.get_by_review_id(review_id)
        if pubmed_results:
            df_data = [{
                "PMID": r.pmid,
                "Title": r.title,
                "Journal": r.journal,
                "Year": r.year,
                "DOI": r.doi
            } for r in pubmed_results]
            st.dataframe(df_data, use_container_width=True)
            
    with tab2:
        scopus_results = scopus_repo.get_by_review_id(review_id)
        if scopus_results:
            df_data = [{
                "Scopus ID": r.scopus_id,
                "Title": r.title,
                "Journal": r.journal,
                "Year": r.year,
                "DOI": r.doi
            } for r in scopus_results]
            st.dataframe(df_data, use_container_width=True)
=======
                # Do not return here, allow results display below

    if st.button("Clear search results"):
        repo.delete_by_review_id(review_id)
        st.session_state.pubmed_results = []  # Clear local state too
        st.success("Search results cleared")
        st.rerun()  # Rerun to reflect cleared results

    # Show existing results
    existing = repo.get_by_review_id(review_id)
    if not existing:
        st.info("No search results available for this review yet.")
        st.stop()  # Stop if no results

    st.session_state.pubmed_results = existing

    st.divider()
    df_data = [
        {
            "PMID": r.pmid,
            "DOI": r.doi,
            "PMC": r.pmc,
            "Title": r.title,
            "Journal": r.journal,
            "Year": r.year,
            "Query": r.query,
        }
        for r in existing
    ]
    st.dataframe(df_data, use_container_width=True)

    if existing:
        if pmid := st.selectbox("Select article:", [r.pmid for r in existing]):
            article = next((r for r in existing if r.pmid == pmid), None)
            if article:
                st.subheader(article.title)
                st.text(f"{article.journal} ({article.year})")
                st.write(article.abstract)
                logger.info("Selected article: {!r}", article)
                st.json(article.model_dump(mode="json"), expanded=True)
>>>>>>> 51577862cfec852c9be7f2326673108c705badc3

    st.page_link(
        "pages/screen_abstracts.py",
        label="Next: Screen Abstracts",
        icon=":material/arrow_forward:",
    )


if "review" not in st.session_state:
    st.error("Please define a systematic review protocol first")
else:
    if "logger_extra_configured" not in st.session_state:
        logger.configure(extra={"review_id": st.session_state.review.id})
        st.session_state.logger_extra_configured = True
    search_page(review_id=st.session_state.review.id)
