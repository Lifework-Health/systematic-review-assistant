"""Old obsolete page, to be deleted."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sr_assistant.app.agents import abstract_screening_chain
from sr_assistant.core.repositories import (
    PubMedRepository,
    ScreeningAbstractRepository,
)
from sr_assistant.core.schemas import ScreeningResponse


def screening_abstracts_page(review_id: UUID) -> None:
    """Abstract screening page."""
    if "abstract_screening_chain" not in st.session_state:
        st.session_state.abstract_screening_chain = abstract_screening_chain
    if "review_id" not in st.session_state:
        st.error("Please select a review first")
        st.stop()

    review_id = st.session_state.review_id
    if "pubmed_repository" not in st.session_state:
        st.session_state.pubmed_repository = PubMedRepository(st.session_state.supabase)
    if "screening_abstract_repository" not in st.session_state:
        st.session_state.screening_abstract_repository = ScreeningAbstractRepository(
            st.session_state.supabase
        )

    # Initialize session state for screening results
    if "screening_results" not in st.session_state:
        st.session_state.screening_results = {}

    # Get search results and existing screening decisions
    search_results = st.session_state.pubmed_repository.get_review_results(review_id)
    screening_results = (
        st.session_state.screening_abstract_repository.get_screening_results(review_id)
    )

    # Create a mapping of search_result_id to screening result
    screened_results = {str(r.search_result_id): r for r in screening_results}

    # Create a DataFrame for display
    results_data = []
    for result in search_results:
        screening_result = screened_results.get(str(result.id))
        results_data.append(
            {
                "ID": result.i,
                "Title": result.title,
                "Year": result.year,
                "Status": "Screened" if screening_result else "Pending",
                "Decision": screening_result.decision.value
                if screening_result
                else None,
                "Confidence": f"{screening_result.confidence_score:.2f}"
                if screening_result
                else None,
            }
        )

    df = pd.DataFrame(results_data)

    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Papers", len(search_results))
    with col2:
        st.metric("Screened", len(screening_results))
    with col3:
        st.metric("Pending", len(search_results) - len(screening_results))

    # Add a button to screen pending papers
    if st.button(
        "Screen Pending Papers", disabled=len(search_results) == len(screening_results)
    ):
        pending_results = [
            r for r in search_results if str(r.id) not in screened_results
        ]

        # Process in batches of 10
        batch_size = 10
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(0, len(pending_results), batch_size):
            batch = pending_results[i : i + batch_size]
            status_text.text(
                f"Screening papers {i+1}-{min(i+batch_size, len(pending_results))} of {len(pending_results)}..."
            )

            # Prepare batch inputs
            batch_inputs = [
                {
                    "research_question": st.session_state.review.question,
                    "inclusion_criteria": st.session_state.review.inclusion_criteria,
                    "exclusion_criteria": st.session_state.review.exclusion_criteria,
                    "title": paper.title,
                    "year": paper.year,
                    "abstract": paper.abstract,
                }
                for paper in batch
            ]

            # Get screening decisions
            batch_results = st.session_state.abstract_screening_chain.batch(
                batch_inputs
            )

            # Store results
            for paper, result in zip(batch, batch_results, strict=False):
                # Use the more conservative decision
                llm1_response: ScreeningResponse = result["llm1_response"]
                llm2_response: ScreeningResponse = result["llm2_response"]

                # If either reviewer is uncertain, use that decision
                if (
                    llm1_response.decision == "uncertain"
                    or llm2_response.decision == "uncertain"
                ):
                    final_response = (
                        llm1_response
                        if llm1_response.decision == "uncertain"
                        else llm2_response
                    )
                # If they disagree (include vs exclude), mark as uncertain
                elif llm1_response.decision != llm2_response.decision:
                    final_response = ScreeningResponse(
                        decision="uncertain",
                        confidence_score=min(
                            llm1_response.confidence_score,
                            llm2_response.confidence_score,
                        ),
                        rationale="Reviewers disagree on decision. Conservative reviewer: "
                        + llm1_response.rationale
                        + "\nComprehensive reviewer: "
                        + llm2_response.rationale,
                        extracted_quotes=llm1_response.extracted_quotes
                        + llm2_response.extracted_quotes,
                        exclusion_reason_categories=None,
                    )
                # Otherwise use the more conservative response
                else:
                    final_response = (
                        llm1_response
                        if llm1_response.confidence_score
                        < llm2_response.confidence_score
                        else llm2_response
                    )

                # Store in database
                screening_result = st.session_state.screening_abstract_repository.create_screening_result(
                    review_id=review_id,
                    search_result_id=paper.id,
                    response=final_response,
                )

                # Update session state
                screened_results[str(paper.id)] = screening_result

            # Update progress
            progress = (i + len(batch)) / len(pending_results)
            progress_bar.progress(progress)

        status_text.text("Screening complete!")
        st.rerun()

    # Display results table with filtering
    st.subheader("Screening Results")

    # Add filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Screened"])
    with col2:
        if status_filter == "Screened":
            decision_filter = st.selectbox(
                "Filter by Decision", ["All", "Include", "Exclude", "Uncertain"]
            )

    # Apply filters
    filtered_df = df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]
    if status_filter == "Screened" and decision_filter != "All":
        filtered_df = filtered_df[filtered_df["Decision"] == decision_filter.lower()]

    # Display table
    st.dataframe(
        filtered_df,
        hide_index=True,
        column_config={
            "ID": st.column_config.TextColumn(
                "ID",
                help="Paper ID",
                width="small",
            ),
            "Title": st.column_config.TextColumn(
                "Title",
                help="Paper title",
                width="large",
            ),
            "Year": st.column_config.TextColumn(
                "Year",
                help="Publication year",
                width="small",
            ),
            "Status": st.column_config.TextColumn(
                "Status",
                help="Screening status",
                width="small",
            ),
            "Decision": st.column_config.TextColumn(
                "Decision",
                help="Screening decision",
                width="small",
            ),
            "Confidence": st.column_config.TextColumn(
                "Confidence",
                help="Decision confidence score",
                width="small",
            ),
        },
    )

    # Show details when a row is selected
    if st.session_state.get("selected_paper_id"):
        selected_id = st.session_state.selected_paper_id
        paper = next((r for r in search_results if str(r.id) == selected_id), None)
        screening_result = screened_results.get(selected_id)

        if paper and screening_result:
            st.subheader("Paper Details")
            st.write(f"**Title:** {paper.title}")
            st.write(f"**Year:** {paper.year}")
            st.write(f"**Journal:** {paper.journal}")
            st.write("**Abstract:**")
            st.write(paper.abstract)

            st.subheader("Screening Decision")
            st.write(f"**Decision:** {screening_result.decision.value}")
            st.write(f"**Confidence:** {screening_result.confidence_score:.2f}")
            st.write("**Rationale:**")
            st.write(screening_result.rationale)

            if screening_result.extracted_quotes:
                st.write("**Supporting Quotes:**")
                for quote in screening_result.extracted_quotes:
                    st.markdown(f"- _{quote}_")

            if screening_result.exclusion_reason_categories:
                st.write("**Exclusion Categories:**")
                for category in screening_result.exclusion_reason_categories:
                    st.markdown(f"- {category}")
