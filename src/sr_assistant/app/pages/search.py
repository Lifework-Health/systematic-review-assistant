from __future__ import annotations

from uuid import UUID

import streamlit as st
from loguru import logger

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

    if submitted:
        with st.status("Searching...", expanded=True) as status:
            try:
                if database == "PubMed":
                    # PubMed search
                    pmids = pubmed_search(search_query, max_results)
                    if not pmids:
                        st.warning("No results found")
                        return

                    records = pubmed_fetch_details(pmids)
                    results = pubmed_repo.store_results(review_id, search_query, records)
                    st.success(f"Found {len(results)} articles in PubMed")
                    
                else:
                    # Scopus search
                    results = scopus_repo.search(search_query, review_id)
                    st.success(f"Found {len(results)} articles in Scopus")

                status.update(label="Search complete", state="complete")
                
                # Store results in session state
                if database == "PubMed":
                    st.session_state.pubmed_results = results
                else:
                    st.session_state.scopus_results = results

            except Exception as e:
                status.update(label="Search failed", state="error")
                st.error(str(e))
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

    st.page_link("pages/screen_abstracts.py", label="Next: Screen Abstracts")


if "review" not in st.session_state:
    st.error("Please define a systematic review protocol first")
else:
    if "logger_extra_configured" not in st.session_state:
        logger.configure(extra={"review_id": st.session_state.review.id})
        st.session_state.logger_extra_configured = True
    search_page(review_id=st.session_state.review.id)
