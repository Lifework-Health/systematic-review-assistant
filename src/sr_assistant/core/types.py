"""Core types for SR assistant.

Anything used as a SQLModel field type cannot be Literal, SQLAlchemy requires column
types to be classes. So use StrEnum/IntEnum/... instead. Literal is fine nested in
values/schemas.

Notes:
    - Any Enum is `Iterable` by default, Literal types need typing.get_args().
    - ``Literal["a", "b", None]`` is a union, i.e., either "a", "b", or None.
      To allow more than one value use ``list[Literal["a", "b", None]]``.
    - Enums can have JSONSchema (TypeAdapter cls method) and property methods, value
      aliases, etc. But a Pydantic RootModel can be very similar to an enum.
"""

from __future__ import annotations

import typing as t
from datetime import datetime, timezone
from enum import StrEnum, auto
from typing import Literal

import annotated_types as at
import uuid6
from pydantic import GetPydanticSchema, WithJsonSchema
from pydantic_core import core_schema

from sr_assistant.app import utils as u

type PMID = t.Annotated[
    str,
    at.Predicate(u.is_pmid),
    at.MinLen(1),
    at.MaxLen(8),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^\d{1,8}$",
            "description": "PubMed ID (PMID) - 1 to 8 digits",
            "examples": ["123456", "12345678"],
        }
    ),
]
"""PubMed ID (PMID) - 1 to 8 digits."""

type PMCID = t.Annotated[
    str,
    at.Predicate(u.is_pmcid),
    at.MinLen(4),
    at.MaxLen(11),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": r"^PMC\d{1,8}$",
            "description": "PubMed Central ID (PMCID) - PMC followed by 1 to 8 digits",
            "examples": ["PMC123456", "PMC12345678"],
        }
    ),
]
"""PubMed Central ID (PMCID) - PMC followed by 1 to 8 digits."""


type UtcDatetime = t.Annotated[
    datetime,
    at.Predicate(u.is_utc_datetime),
    at.Timezone(timezone.utc),
    WithJsonSchema(
        {
            "type": "string",
            "format": "date-time",
            "description": "UTC datetime",
            "examples": ["2024-02-07T12:00:00Z"],
        }
    ),
]

type UUID7 = t.Annotated[
    uuid6.UUID,
    GetPydanticSchema(
        get_pydantic_core_schema=lambda _,
        handler: core_schema.with_info_plain_validator_function(
            lambda val, info: u.validate_uuid(
                uuid6.UUID(val) if info.mode == "json" else val, version=7
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda val, info: str(val) if info.mode == "json" else val,
                info_arg=True,
            ),
        ),
        get_pydantic_json_schema=lambda _, handler: {
            **handler(core_schema.str_schema()),
            "format": "uuid7",
        },
    ),
]
"""Pydatic/SQLModel/SQLAlchemy compatible UUID7 type.

Don't remember where this is from. A GitHub issue comment.
- Could be improved with validators and maybe using TypeAdapter:
``TypeAdapter(UUID7).validate_python(input)"""


class ScreeningDecisionType(StrEnum):
    """Screening decision enum type.

    Attributes:
        include: Include the study in the systematic review.
        exclude: Exclude the study from the systematic review.
        uncertain: Mark the study as uncertain.
    """

    INCLUDE = auto()
    """Include the study in the systematic review."""
    EXCLUDE = auto()
    """Exclude the study from the systematic review."""
    UNCERTAIN = auto()
    """Mark the study as uncertain."""


class CitationFormat(StrEnum):
    """Standardized citation formats supported by academic databases.

    Different disciplines and journals prefer different citation formats. This
    classification helps ensure consistent citation export across databases.

    Examples:
        >>> ref = Reference(format=CitationFormat.VANCOUVER)
        >>> print(ref.format())
        'Smith J, et al. Cancer Research. 2023;12(3):45-50.'
        >>> ref.format = CitationFormat.APA
        >>> print(ref.format())
        'Smith, J., & Jones, M. (2023). Cancer research. Journal, 12(3), 45-50.'

    See Also:
        `Citation Guide <https://www.nlm.nih.gov/bsd/uniform_requirements.html>`_
    """

    VANCOUVER = auto()
    """International Committee of Medical Journal Editors (ICMJE) format.

    Standard format for medical literature, used by PubMed and most medical journals.
    """

    APA = auto()
    """American Psychological Association format.

    Used in psychology, education, and social sciences. Standard for PsycINFO.
    """

    HARVARD = auto()
    """Harvard citation format.

    Common in business and humanities. Used by many European journals.
    """

    IEEE = auto()
    """Institute of Electrical and Electronics Engineers format.

    Standard for engineering and computer science publications.
    """

    CHICAGO = auto()
    """Chicago Manual of Style format.

    Common in humanities and some social sciences.
    """

    MLA = auto()
    """Modern Language Association format.

    Standard format for humanities, especially literature and linguistics.
    """

    @property
    def description(self) -> str:
        """Returns detailed description of the citation format.

        Returns:
            str: Format description and typical use cases.
        """
        descriptions = {
            CitationFormat.VANCOUVER: (
                "Numerical citation format used in medical and scientific "
                "publications. Follows ICMJE recommendations."
            ),
            CitationFormat.APA: (
                "Author-date format used in social sciences. Currently in 7th "
                "edition. Features DOIs and URLs for electronic sources."
            ),
            CitationFormat.HARVARD: (
                "Author-date format popular in universities. Note that 'Harvard' "
                "has several variants based on institution."
            ),
            CitationFormat.IEEE: (
                "Numerical format with specific conventions for technical "
                "documents. Used in engineering fields."
            ),
            CitationFormat.CHICAGO: (
                "Offers both author-date and notes-bibliography systems. "
                "Currently in 17th edition."
            ),
            CitationFormat.MLA: (
                "Author-page format used in humanities. Currently in 9th "
                "edition. Emphasizes print sources."
            ),
        }
        return descriptions[self]

    @property
    def example(self) -> str:
        """Returns an example citation in this format.

        Returns:
            str: Example formatted citation.
        """
        examples = {
            CitationFormat.VANCOUVER: (
                "1. Smith J, Jones M, Liu X. Cancer patterns. N Engl J Med. "
                "2023;380(1):23-34. doi: 10.1056/nejm.2023.1234"
            ),
            CitationFormat.APA: (
                "Smith, J., Jones, M., & Liu, X. (2023). Cancer patterns in "
                "global populations. New England Journal of Medicine, 380(1), "
                "23-34. https://doi.org/10.1056/nejm.2023.1234"
            ),
            CitationFormat.HARVARD: (
                "Smith, J., Jones, M. and Liu, X., 2023. Cancer patterns in "
                "global populations. New England Journal of Medicine, 380(1), "
                "pp.23-34."
            ),
            CitationFormat.IEEE: (
                '[1] J. Smith, M. Jones, and X. Liu, "Cancer patterns in '
                'global populations," N. Engl. J. Med., vol. 380, no. 1, '
                "pp. 23-34, Jan. 2023."
            ),
            CitationFormat.CHICAGO: (
                'Smith, John, Mary Jones, and Xiao Liu. "Cancer Patterns in '
                'Global Populations." New England Journal of Medicine 380, '
                "no. 1 (January 2023): 23-34."
            ),
            CitationFormat.MLA: (
                'Smith, John, et al. "Cancer Patterns in Global Populations." '
                "New England Journal of Medicine, vol. 380, no. 1, Jan. 2023, "
                "pp. 23-34."
            ),
        }
        return examples[self]


"""SR search strategy and searching related types.

AI generated types for search strategy and searching. Not in use in the prototype yet
and needs refactoring. E.g., study designs missing, etc.
"""


class DatabaseType(StrEnum):
    """Classifies academic and scientific databases by their primary content type.

    This classification helps determine appropriate search strategies and expected
    content types. While databases may serve multiple purposes, we designate the
    primary type here for systematic review planning.

    See Also:
        :class:`DatabasePlatform`: For information about access platforms.
        `Systematic Review Types <https://www.cochranelibrary.com/about/about-cochrane-reviews>`_
    """

    BIBLIOGRAPHIC = auto()
    """Standard bibliographic databases containing primarily journal articles and conference proceedings."""

    CLINICAL_TRIALS = auto()
    """Specialized databases focused on clinical trial registrations and results."""

    GREY_LITERATURE = auto()
    """Sources for conference abstracts, dissertations, and other non-journal content."""

    CITATION_INDEX = auto()
    """Citation-focused databases that track article references and citations."""


class DatabasePlatform(StrEnum):
    """Platform interfaces through which databases can be accessed.

    In academic/scientific database access, the same database content may be available
    through different platforms. Each platform has unique characteristics affecting:
        * Search syntax and capabilities
        * Field codes and operators
        * Authentication methods
        * Rate limits and quotas
        * Results format and export options

    Examples:
        * MEDLINE content via PubMed (native) vs Ovid platforms
        * PsycINFO accessed through Ovid vs EBSCO interfaces

    Note:
        Platform choice can significantly impact systematic review methodology due to
        differences in search syntax and capabilities.
    """

    NATIVE = auto()
    """Database's own platform (e.g., PubMed interface for MEDLINE content)."""

    OVID = auto()
    """Wolters Kluwer's Ovid platform, known for advanced search syntax and medical focus.

    See Also:
        `Ovid Syntax Guide <https://ospguides.ovid.com/OSPguides/medline.htm>`_
    """

    EBSCO = auto()
    """EBSCO platform, widely used in academic libraries, supports multiple databases."""

    PROQUEST = auto()
    """ProQuest platform, common in academic institutions, strong in social sciences."""

    WILEY = auto()
    """Wiley Online Library, primary access point for Cochrane Library and Wiley content."""

    @property
    def display_name(self) -> str:
        """Returns human-readable platform name with proper capitalization.

        Returns:
            str: Formatted display name for UI presentation.
        """
        display_names = {
            DatabasePlatform.NATIVE: "Native Interface",
            DatabasePlatform.OVID: "Ovid",
            DatabasePlatform.EBSCO: "EBSCO",
            DatabasePlatform.PROQUEST: "ProQuest",
            DatabasePlatform.WILEY: "Wiley Online Library",
        }
        return display_names[self]


class FieldType(StrEnum):
    """Classifies database search fields for cross-platform compatibility.

    This classification system enables:
        * Field mapping between different databases
        * Query translation between platforms
        * Standardized search strategy development
        * Consistent results processing

    Note:
        Different platforms often use varying field codes for the same concept.
        For example, title searches might use:
            * PubMed: [ti]
            * Ovid: .ti
            * EBSCO: TI

    See Also:
        :class:`SearchField`: For field implementation details.
    """

    TITLE = auto()
    """Article title field, typically high-precision search target."""

    ABSTRACT = auto()
    """Abstract text, important for comprehensive searching."""

    KEYWORD = auto()
    """Author-assigned keywords or uncontrolled terms."""

    CONTROLLED_VOCAB = auto()
    """Controlled vocabulary terms (e.g., MeSH, Emtree) for precise subject searching."""

    PUBLICATION_TYPE = auto()
    """Document type classification (e.g., review, clinical trial, meta-analysis)."""

    AUTHOR = auto()
    """Author name fields for author-specific searches."""

    JOURNAL = auto()
    """Source publication name for journal-specific searches."""

    YEAR = auto()
    """Publication year for date-range limitations."""

    LANGUAGE = auto()
    """Publication language for language-specific filtering."""

    ALL = auto()
    """Multi-field search across multiple fields (implementation varies by platform)."""


class StudyType(StrEnum):
    """Classification of research study types in evidence-based medicine.

    Study types are hierarchically organized based on their level of evidence,
    with each type having specific methodological characteristics. This classification
    follows the Oxford Centre for Evidence-Based Medicine (OCEBM) framework while
    including additional types relevant to systematic reviews.

    Examples:
        >>> study = Study(type=StudyType.RCT)
        >>> study.type.evidence_level
        1
        >>> study.type.mesh_term
        'Randomized Controlled Trial[pt]'

    See Also:
        `OCEBM Levels of Evidence <https://www.cebm.ox.ac.uk/resources/levels-of-evidence/ocebm-levels-of-evidence>`_
    """

    RCT = auto()
    """Randomized Controlled Trial - experimental study with random allocation to intervention groups."""

    SYSTEMATIC_REVIEW = auto()
    """Systematic Review - structured review following explicit methodology to synthesize evidence."""

    META_ANALYSIS = auto()
    """Meta-Analysis - statistical combination of results from multiple studies."""

    COHORT = auto()
    """Cohort Study - observational study following groups over time to assess outcomes."""

    CASE_CONTROL = auto()
    """Case-Control Study - retrospective comparison of groups with and without an outcome."""

    CROSS_SECTIONAL = auto()
    """Cross-Sectional Study - observational study examining population at a single time point."""

    QUALITATIVE = auto()
    """Qualitative Research - non-statistical study of experiences, behaviors, or phenomena."""

    ECONOMIC = auto()
    """Economic Evaluation - analysis of healthcare interventions' cost-effectiveness."""

    DIAGNOSTIC = auto()
    """Diagnostic Accuracy Study - evaluation of diagnostic tests against reference standards."""

    @property
    def evidence_level(self) -> int:
        """Returns the Oxford CEBM level of evidence (1-5, lower is better).

        The evidence level indicates the strength of evidence provided by this study type,
        following the Oxford Centre for Evidence-Based Medicine hierarchy.

        Returns:
            int: Evidence hierarchy level where 1 is highest quality and 5 is lowest
        """
        levels = {
            StudyType.SYSTEMATIC_REVIEW: 1,  # With homogeneous RCTs
            StudyType.RCT: 1,  # Well-designed individual RCT
            StudyType.META_ANALYSIS: 1,  # When combining similar RCTs
            StudyType.COHORT: 2,  # Prospective cohort studies
            StudyType.CASE_CONTROL: 3,  # Well-designed case-control
            StudyType.CROSS_SECTIONAL: 4,  # Cross-sectional studies
            StudyType.QUALITATIVE: 5,  # Qualitative studies
            StudyType.ECONOMIC: 2,  # Based on level 1-2 studies
            StudyType.DIAGNOSTIC: 2,  # Well-designed diagnostic studies
        }
        return levels[self]

    @property
    def mesh_term(self) -> str:
        """Returns the PubMed MeSH term for this study type.

        Provides the proper PubMed search syntax combining publication type [pt]
        and MeSH [mesh] terms as appropriate for comprehensive retrieval.

        Returns:
            str: PubMed-style search syntax for this study type
        """
        terms = {
            StudyType.RCT: (
                "Randomized Controlled Trial[pt] OR Controlled Clinical Trial[pt] OR "
                "randomized[tiab] OR randomised[tiab] OR placebo[tiab] OR "
                "randomly[tiab] OR trial[tiab]"
            ),
            StudyType.SYSTEMATIC_REVIEW: (
                "Systematic Review[pt] OR Meta-Analysis[pt] OR "
                "systematic[sb] OR Review Literature as Topic[mesh]"
            ),
            StudyType.META_ANALYSIS: (
                "Meta-Analysis[pt] OR Meta-Analysis as Topic[mesh] OR "
                "meta-analysis[tiab] OR metaanalysis[tiab]"
            ),
            StudyType.COHORT: (
                "Observational Study[pt] OR Cohort Studies[mesh] OR "
                "cohort[tiab] OR longitudinal[tiab] OR prospective[tiab] OR "
                "retrospective[tiab]"
            ),
            StudyType.CASE_CONTROL: (
                "Case-Control Studies[mesh] OR case control[tiab] OR case-control[tiab]"
            ),
            StudyType.CROSS_SECTIONAL: (
                "Cross-Sectional Studies[mesh] OR cross-sectional[tiab] OR "
                "prevalence[tiab]"
            ),
            StudyType.QUALITATIVE: (
                "Qualitative Research[mesh] OR qualitative[tiab] OR "
                "interview*[tiab] OR focus group*[tiab] OR ethnograph*[tiab] OR "
                "grounded theory[tiab] OR narrative[tiab]"
            ),
            StudyType.ECONOMIC: (
                "Economics[mesh] OR Costs and Cost Analysis[mesh] OR "
                "cost effective*[tiab] OR economic*[tiab] OR cost benefit[tiab] OR "
                "health utilit*[tiab]"
            ),
            StudyType.DIAGNOSTIC: (
                "Diagnostic Tests, Routine[mesh] OR Sensitivity and Specificity[mesh] OR "
                "diagnostic accuracy[tiab] OR sensitivity[tiab] OR specificity[tiab] OR "
                "predictive value*[tiab] OR likelihood ratio*[tiab]"
            ),
        }
        return terms[self]

    @property
    def emtree_term(self) -> str:
        """Returns the Embase Emtree term for this study type.

        Provides Embase-specific syntax combining Emtree terms and
        free text to ensure comprehensive retrieval.

        Returns:
            str: Embase-style search syntax for this study type
        """
        terms = {
            StudyType.RCT: (
                "'randomized controlled trial'/exp OR 'controlled clinical trial'/exp OR "
                "random*:ti,ab OR placebo:ti,ab OR 'clinical trial':ti,ab"
            ),
            StudyType.SYSTEMATIC_REVIEW: (
                "'systematic review'/exp OR 'meta analysis'/exp OR "
                "'systematic review':ti,ab OR 'meta analysis':ti,ab"
            ),
            StudyType.META_ANALYSIS: (
                "'meta analysis'/exp OR 'systematic review'/exp OR "
                "metaanalysis:ti,ab OR 'meta analysis':ti,ab OR 'systematic review':ti,ab"
            ),
            StudyType.COHORT: (
                "'cohort analysis'/exp OR 'longitudinal study'/exp OR "
                "cohort:ti,ab OR longitudinal:ti,ab OR prospective:ti,ab OR "
                "retrospective:ti,ab"
            ),
            StudyType.CASE_CONTROL: (
                "'case control study'/exp OR 'case control':ti,ab OR "
                "'case-control':ti,ab"
            ),
            StudyType.CROSS_SECTIONAL: (
                "'cross-sectional study'/exp OR 'prevalence study'/exp OR "
                "'cross sectional':ti,ab OR prevalence:ti,ab"
            ),
            StudyType.QUALITATIVE: (
                "'qualitative research'/exp OR qualitative:ti,ab OR interview*:ti,ab OR "
                "'focus group':ti,ab OR ethnograph*:ti,ab OR 'grounded theory':ti,ab"
            ),
            StudyType.ECONOMIC: (
                "'health economics'/exp OR 'cost effectiveness analysis'/exp OR "
                "'cost benefit analysis'/exp OR economic*:ti,ab OR "
                "'cost effective*':ti,ab OR 'cost benefit':ti,ab"
            ),
            StudyType.DIAGNOSTIC: (
                "'diagnostic accuracy'/exp OR 'diagnostic test'/exp OR "
                "'sensitivity and specificity'/exp OR 'diagnostic accuracy':ti,ab OR "
                "sensitivity:ti,ab OR specificity:ti,ab"
            ),
        }
        return terms[self]

    @property
    def display_name(self) -> str:
        """Returns formatted display name for UI presentation.

        Provides consistent, human-readable names for use in user interfaces
        and documentation.

        Returns:
            str: Human-readable study type name
        """
        names = {
            StudyType.RCT: "Randomized Controlled Trial",
            StudyType.SYSTEMATIC_REVIEW: "Systematic Review",
            StudyType.META_ANALYSIS: "Meta-Analysis",
            StudyType.COHORT: "Cohort Study",
            StudyType.CASE_CONTROL: "Case-Control Study",
            StudyType.CROSS_SECTIONAL: "Cross-Sectional Study",
            StudyType.QUALITATIVE: "Qualitative Research",
            StudyType.ECONOMIC: "Economic Evaluation",
            StudyType.DIAGNOSTIC: "Diagnostic Accuracy Study",
        }
        return names[self]

    @property
    def description(self) -> str:
        """Returns detailed description of the study type.

        Provides comprehensive explanations suitable for documentation,
        training materials, and contextual help.

        Returns:
            str: Comprehensive explanation suitable for documentation
        """
        descriptions = {
            StudyType.RCT: (
                "Experimental study where participants are randomly allocated to "
                "intervention or control groups. Considered the gold standard for "
                "evaluating intervention effectiveness. Random allocation helps ensure "
                "groups are comparable at baseline, minimizing selection bias and "
                "confounding."
            ),
            StudyType.SYSTEMATIC_REVIEW: (
                "Comprehensive literature review that systematically identifies, "
                "appraises, and synthesizes all relevant studies on a specific "
                "research question. Follows explicit, pre-specified methodology to "
                "minimize bias and provide reliable evidence synthesis."
            ),
            StudyType.META_ANALYSIS: (
                "Statistical analysis that combines results from multiple independent "
                "studies. Increases statistical power and precision of effect estimates. "
                "Often conducted as part of a systematic review, but can be performed "
                "independently."
            ),
            StudyType.COHORT: (
                "Observational study that follows a group of people over time to "
                "examine associations between exposures and outcomes. Can be "
                "prospective (forward-looking) or retrospective (historical). Useful "
                "for studying natural history and risk factors."
            ),
            StudyType.CASE_CONTROL: (
                "Observational study that compares people with a specific outcome "
                "(cases) to those without the outcome (controls) to identify potential "
                "risk factors. Efficient for studying rare outcomes or diseases. "
                "Retrospective in nature."
            ),
            StudyType.CROSS_SECTIONAL: (
                "Observational study that examines the relationship between variables "
                "of interest in a population at a single point in time. Useful for "
                "determining prevalence and identifying associations. Cannot establish "
                "temporal relationships."
            ),
            StudyType.QUALITATIVE: (
                "Research methodology that explores human experiences, behaviors, and "
                "social phenomena through non-numerical data. Uses methods like "
                "interviews, focus groups, and observation. Important for understanding "
                "complex social and behavioral aspects of health."
            ),
            StudyType.ECONOMIC: (
                "Analysis that evaluates both the costs and consequences of healthcare "
                "interventions. Includes cost-effectiveness, cost-utility, cost-benefit, "
                "and cost-minimization analyses. Essential for healthcare decision-making "
                "and resource allocation."
            ),
            StudyType.DIAGNOSTIC: (
                "Study that assesses the accuracy of a diagnostic test, screening tool, "
                "or clinical assessment method. Typically compares index test results "
                "with a reference standard. Reports measures like sensitivity, "
                "specificity, and predictive values."
            ),
        }
        return descriptions[self]

    @property
    def search_filters(self) -> dict[DatabaseType, str]:
        """Returns database-specific methodology filters.

        Provides optimized search syntax for different database types,
        accounting for their specific features and vocabulary.

        Returns:
            dict[DatabaseType, str]: Search syntax for major databases
        """
        return {
            DatabaseType.BIBLIOGRAPHIC: self.mesh_term,
            DatabaseType.CLINICAL_TRIALS: (
                f"study_type={self.name.lower()}"
                if self == StudyType.RCT
                else "study_type=interventional"
            ),
            DatabaseType.CITATION_INDEX: self._web_of_science_term,
            DatabaseType.GREY_LITERATURE: self._proquest_term,
        }

    @property
    def _web_of_science_term(self) -> str:
        """Returns Web of Science search syntax for this study type."""
        terms = {
            StudyType.RCT: (
                "TS=(random* NEAR/2 (trial* OR allocat* OR assign*)) OR "
                "TS=(controlled NEAR/2 trial*)"
            ),
            StudyType.SYSTEMATIC_REVIEW: (
                "TS=('systematic review' OR 'systematic literature review' OR "
                "meta-analysis)"
            ),
            StudyType.META_ANALYSIS: "TS=(meta-analysis OR metaanalysis)",
            StudyType.COHORT: (
                "TS=(cohort NEAR/2 (study OR studies)) OR "
                "TS=(longitudinal NEAR/2 (study OR studies))"
            ),
            StudyType.CASE_CONTROL: "TS=('case control' OR 'case-control')",
            StudyType.CROSS_SECTIONAL: (
                "TS=('cross sectional' OR 'cross-sectional' OR prevalence)"
            ),
            StudyType.QUALITATIVE: (
                "TS=(qualitative OR interview* OR 'focus group*' OR ethnograph* OR "
                "'grounded theory')"
            ),
            StudyType.ECONOMIC: (
                "TS=('cost effective*' OR 'cost benefit' OR 'economic evaluation' OR "
                "'cost utility')"
            ),
            StudyType.DIAGNOSTIC: (
                "TS=('diagnostic accuracy' OR sensitivity OR specificity OR "
                "'predictive value*')"
            ),
        }
        return terms[self]

    @property
    def _proquest_term(self) -> str:
        """Returns ProQuest search syntax for this study type."""
        terms = {
            StudyType.RCT: (
                "NOFT(random* NEAR/3 (trial* OR allocat* OR assign*)) OR "
                "NOFT(controlled NEAR/3 trial*)"
            ),
            StudyType.SYSTEMATIC_REVIEW: (
                "NOFT('systematic review' OR 'systematic literature review' OR "
                "meta-analysis)"
            ),
            StudyType.META_ANALYSIS: "NOFT(meta-analysis OR metaanalysis)",
            StudyType.COHORT: (
                "NOFT(cohort NEAR/3 (study OR studies)) OR "
                "NOFT(longitudinal NEAR/3 (study OR studies))"
            ),
            StudyType.CASE_CONTROL: (
                "NOFT('case control' OR 'case-control' NEAR/3 (study OR studies))"
            ),
            StudyType.CROSS_SECTIONAL: (
                "NOFT('cross sectional' OR 'cross-sectional' OR prevalence NEAR/3 "
                "(study OR studies))"
            ),
            StudyType.QUALITATIVE: (
                "NOFT(qualitative OR interview* OR 'focus group*' OR ethnograph* OR "
                "'grounded theory' OR phenomenolog*)"
            ),
            StudyType.ECONOMIC: (
                "NOFT('cost effective*' OR 'cost benefit' OR 'economic evaluation' OR "
                "'cost utility' OR 'health economics')"
            ),
            StudyType.DIAGNOSTIC: (
                "NOFT('diagnostic accuracy' OR 'diagnostic test*' OR sensitivity OR "
                "specificity OR 'predictive value*' OR 'likelihood ratio*')"
            ),
        }

        return terms[self]


type ValidationRule = dict[str, str | bool | dict[str, t.Any]]
"""Validation rule for search terms."""


class TermType(StrEnum):
    """Classification of search terms by their role and behavior in search strategies.

    Search terms in systematic reviews can take various forms, each with specific
    syntax rules and search behaviors. This classification helps in:
        * Validating term syntax
        * Guiding strategy development
        * Translating between databases
        * Optimizing search precision and recall

    Examples:
        >>> term = SearchTerm(type=TermType.TRUNCATED, value="therap*")
        >>> term.type.is_valid(term.value)
        True
        >>> print(term.type.syntax_pattern)
        r'.*[*$]'

    See Also:
        `Systematic Review Handbook Ch 4.4.4 <https://training.cochrane.org/handbook/current/chapter-04-4>`_
    """

    EXACT = auto()
    """Exact phrase matching requiring precise term presence."""

    TRUNCATED = auto()
    """Terms using wildcards (*) for variant retrieval."""

    PROXIMITY = auto()
    """Terms combined with proximity operators (NEAR, ADJ, WITHIN)."""

    PHRASE = auto()
    """Multi-word phrases requiring specific handling."""

    CONTROLLED = auto()
    """Controlled vocabulary terms from thesauri like MeSH."""

    FREE_TEXT = auto()
    """Natural language terms for comprehensive retrieval."""

    SYNONYMS = auto()
    """Alternative terms representing the same concept."""

    BOOLEAN = auto()
    """Terms explicitly combined with AND, OR, NOT operators."""

    @property
    def syntax_pattern(self) -> str:
        """Returns regex pattern for validating term syntax.

        Provides regular expressions to validate term formatting according
        to type-specific rules.

        Returns:
            str: Regular expression pattern for term validation
        """
        patterns = {
            TermType.EXACT: r"^[^*$]+$",  # No wildcards allowed
            TermType.TRUNCATED: r".*[*$]",  # Must end with * or $
            TermType.PROXIMITY: r".+\s+(?:NEAR|ADJ|WITHIN)\d*\s+.+",
            TermType.PHRASE: r'^".+"$|^{.+}$',  # Quoted or braced
            TermType.CONTROLLED: r"^[A-Z][A-Za-z\s-]+(/exp)?$",  # CamelCase with optional /exp
            TermType.FREE_TEXT: r".+",  # Any non-empty string
            TermType.SYNONYMS: r".+",  # Any non-empty string
            TermType.BOOLEAN: r".+\s+(?:AND|OR|NOT)\s+.+",
        }
        return patterns[self]

    @property
    def validation_rules(self) -> list[ValidationRule]:
        """Returns list of validation rules for terms of this type.

        Defines constraints and requirements for term validity beyond
        basic syntax patterns.

        Returns:
            list[ValidationRule]: List of validation rules to apply
        """
        rules = {
            TermType.EXACT: [
                {
                    "rule": "no_wildcards",
                    "message": "Exact terms cannot contain wildcards",
                },
                {
                    "rule": "no_operators",
                    "message": "Exact terms cannot contain operators",
                },
                {"min_length": 3, "message": "Term must be at least 3 characters"},
            ],
            TermType.TRUNCATED: [
                {"rule": "valid_truncation", "message": "Must end with * or $"},
                {
                    "min_stem": 3,
                    "message": "Must have at least 3 characters before truncation",
                },
            ],
            TermType.PROXIMITY: [
                {
                    "rule": "valid_operator",
                    "message": "Must use valid proximity operator",
                },
                {"rule": "valid_distance", "message": "Distance must be 1-9"},
                {"terms": 2, "message": "Must have exactly two terms"},
            ],
            TermType.PHRASE: [
                {"rule": "matched_quotes", "message": "Quotes must be matched"},
                {"min_words": 2, "message": "Must contain at least two words"},
                {"max_words": 10, "message": "Should not exceed 10 words"},
            ],
            TermType.CONTROLLED: [
                {
                    "rule": "vocabulary_match",
                    "message": "Must match controlled vocabulary",
                },
                {"rule": "proper_case", "message": "Must use proper capitalization"},
            ],
            TermType.FREE_TEXT: [
                {"min_length": 3, "message": "Term must be at least 3 characters"},
                {"rule": "no_noise_words", "message": "Avoid common noise words"},
            ],
            TermType.SYNONYMS: [
                {"min_terms": 2, "message": "Must provide at least two synonyms"},
                {"rule": "unique_terms", "message": "Synonyms must be unique"},
            ],
            TermType.BOOLEAN: [
                {"rule": "valid_operator", "message": "Must use AND, OR, or NOT"},
                {"rule": "balanced_expr", "message": "Expression must be balanced"},
            ],
        }
        return rules[self]

    @property
    def display_name(self) -> str:
        """Returns formatted display name for UI presentation.

        Provides consistent, human-readable names for use in interfaces
        and documentation.

        Returns:
            str: Human-readable term type name
        """
        names = {
            TermType.EXACT: "Exact Match",
            TermType.TRUNCATED: "Truncated Term",
            TermType.PROXIMITY: "Proximity Search",
            TermType.PHRASE: "Phrase Search",
            TermType.CONTROLLED: "Controlled Vocabulary",
            TermType.FREE_TEXT: "Free Text",
            TermType.SYNONYMS: "Synonym Group",
            TermType.BOOLEAN: "Boolean Expression",
        }
        return names[self]

    @property
    def description(self) -> str:
        """Returns detailed description of the term type.

        Provides comprehensive explanations suitable for documentation,
        training materials, and contextual help.

        Returns:
            str: Comprehensive explanation suitable for documentation
        """
        descriptions = {
            TermType.EXACT: (
                "Terms that must appear exactly as specified in the search results. "
                "No automatic variant matching is performed. Useful for specific "
                "phrases or when variant retrieval would reduce precision. Most "
                "restrictive search type."
            ),
            TermType.TRUNCATED: (
                "Terms using wildcards (*) to retrieve variants. The asterisk "
                "represents any number of characters. For example, therap* retrieves "
                "therapy, therapies, therapeutic, etc. Essential for comprehensive "
                "retrieval of variant word forms."
            ),
            TermType.PROXIMITY: (
                "Terms combined with operators specifying their maximum distance "
                "apart. More precise than phrase searching but more flexible than "
                "exact matches. Operators vary by database (NEAR/n, ADJn, WITHIN n). "
                "Crucial for precise concept searching."
            ),
            TermType.PHRASE: (
                "Multi-word expressions treated as a unit. Usually enclosed in "
                "quotes or braces. Databases may handle phrases differently, some "
                "allowing internal wildcards or variant word forms. More precise "
                "than individual word searching."
            ),
            TermType.CONTROLLED: (
                "Terms from a database's controlled vocabulary (thesaurus). These "
                "standardized subject terms help overcome natural language "
                "variations. May include automatic term explosion to retrieve "
                "narrower concepts. Essential for systematic searching."
            ),
            TermType.FREE_TEXT: (
                "Natural language terms searched across multiple fields. Most "
                "flexible search type, but may retrieve irrelevant results. "
                "Important for comprehensive retrieval and for concepts not well "
                "covered by controlled vocabulary."
            ),
            TermType.SYNONYMS: (
                "Groups of equivalent terms representing the same concept. Used "
                "to build comprehensive search blocks. May include spelling "
                "variants, abbreviations, and related terms. Essential for "
                "high-sensitivity searching."
            ),
            TermType.BOOLEAN: (
                "Terms explicitly combined using AND, OR, NOT operators. AND "
                "narrows results requiring all terms, OR broadens retrieving "
                "any terms, NOT excludes terms. Forms the logical structure "
                "of search strategies."
            ),
        }
        return descriptions[self]

    @property
    def usage_guidance(self) -> str:
        """Returns guidance on when and how to use this term type.

        Provides best practices and recommendations for effective use
        in search strategies.

        Returns:
            str: Usage guidance and best practices
        """
        guidance = {
            TermType.EXACT: (
                "Use for:\n"
                "* Specific multi-word phrases where word order matters\n"
                "* When variant retrieval would reduce precision\n"
                "* Database-specific codes or identifiers\n"
                "Avoid for:\n"
                "* Single words (use truncation instead)\n"
                "* Concepts with many variant expressions"
            ),
            TermType.TRUNCATED: (
                "Use for:\n"
                "* Capturing different word endings (singular/plural)\n"
                "* Retrieved variant spellings\n"
                "* Increasing sensitivity systematically\n"
                "Consider:\n"
                "* Minimum 3-4 characters before truncation\n"
                "* Both British and American spellings\n"
                "* Internal truncation for complex variants"
            ),
            TermType.PROXIMITY: (
                "Use for:\n"
                "* Related concepts that should appear near each other\n"
                "* More precise than AND but more flexible than phrases\n"
                "* When word order may vary\n"
                "Consider:\n"
                "* Appropriate distance (usually 2-5 words)\n"
                "* Database-specific syntax variations\n"
                "* Word order requirements"
            ),
            TermType.PHRASE: (
                "Use for:\n"
                "* Established multi-word terms\n"
                "* When word order is important\n"
                "* Technical or scientific terminology\n"
                "Consider:\n"
                "* Database phrase handling differences\n"
                "* Alternative word orders\n"
                "* Whether proximity would be more appropriate"
            ),
            TermType.CONTROLLED: (
                "Use for:\n"
                "* Major concepts in search strategy\n"
                "* When available in database thesaurus\n"
                "* Systematic concept retrieval\n"
                "Consider:\n"
                "* Explosion vs. focused terms\n"
                "* Thesaurus hierarchy\n"
                "* Combining with free text"
            ),
            TermType.FREE_TEXT: (
                "Use for:\n"
                "* New or emerging concepts\n"
                "* Complementing controlled vocabulary\n"
                "* Comprehensive retrieval\n"
                "Consider:\n"
                "* All relevant variants\n"
                "* Multiple search fields\n"
                "* Potential noise terms"
            ),
            TermType.SYNONYMS: (
                "Use for:\n"
                "* Building comprehensive concept blocks\n"
                "* Including all variant expressions\n"
                "* International spelling variations\n"
                "Consider:\n"
                "* Common abbreviations\n"
                "* Professional vs. lay terminology\n"
                "* Regional variations"
            ),
            TermType.BOOLEAN: (
                "Use for:\n"
                "* Combining concept blocks\n"
                "* Structuring complex strategies\n"
                "* Precision adjustments\n"
                "Consider:\n"
                "* Operator precedence\n"
                "* Grouping with parentheses\n"
                "* Impact on sensitivity/precision"
            ),
        }
        return guidance[self]

    @property
    def platform_syntax(self) -> dict[str, str]:
        """Returns platform-specific syntax examples.

        Provides examples of correct syntax for different database platforms,
        helping with search strategy translation.

        Returns:
            dict[str, str]: Platform-specific syntax examples
        """
        syntax = {
            TermType.EXACT: {
                "pubmed": '"exact phrase"',
                "ovid": '"exact phrase"',
                "embase": "'exact phrase'",
                "proquest": "EXACT('exact phrase')",
            },
            TermType.TRUNCATED: {
                "pubmed": "therap*",
                "ovid": "therap$",
                "embase": "therap*",
                "proquest": "therap*",
            },
            TermType.PROXIMITY: {
                "pubmed": "cancer AND therapy",  # PubMed lacks true proximity
                "ovid": "cancer adj3 therapy",
                "embase": "cancer NEAR/3 therapy",
                "proquest": "cancer NEAR/3 therapy",
            },
            TermType.PHRASE: {
                "pubmed": '"gene therapy"',
                "ovid": '"gene therapy"',
                "embase": "'gene therapy'",
                "proquest": "gene therapy",
            },
            TermType.CONTROLLED: {
                "pubmed": "Neoplasms[mesh]",
                "ovid": "exp Neoplasms/",
                "embase": "'neoplasm'/exp",
                "proquest": "MESH(Neoplasms)",
            },
            TermType.FREE_TEXT: {
                "pubmed": "cancer[tiab]",
                "ovid": "cancer.ti,ab.",
                "embase": "cancer:ti,ab",
                "proquest": "NOFT(cancer)",
            },
            TermType.SYNONYMS: {
                "pubmed": "(cancer OR neoplasm* OR tumor*)",
                "ovid": "(cancer or neoplasm$ or tumor$)",
                "embase": "(cancer OR neoplasm* OR tumor*)",
                "proquest": "(cancer OR neoplasm* OR tumor*)",
            },
            TermType.BOOLEAN: {
                "pubmed": "(cancer AND therapy) NOT pediatric",
                "ovid": "(cancer and therapy) not pediatric",
                "embase": "(cancer AND therapy) NOT pediatric",
                "proquest": "(cancer AND therapy) NOT pediatric",
            },
        }
        return syntax[self]


type FilterRecommendation = dict[str, str | bool | list[str]]


class BlockPurpose(StrEnum):
    """Purpose classification for search strategy blocks in systematic reviews.

    Search blocks are logical groupings of search terms that represent distinct
    concepts in a systematic review search strategy. This classification helps:
        * Structure search strategies systematically
        * Guide concept development
        * Ensure comprehensive coverage
        * Support strategy validation

    Examples:
        >>> block = SearchBlock(purpose=BlockPurpose.POPULATION)
        >>> block.purpose.pico_element
        'P'
        >>> print(block.purpose.combination_logic)
        'AND with other PICO elements, OR within block'

    See Also:
        `PRISMA-S Guidelines <https://doi.org/10.31219/osf.io/sfc38>`_
    """

    POPULATION = auto()
    """Target population or patient group being studied."""

    INTERVENTION = auto()
    """Treatment, exposure, or intervention being evaluated."""

    COMPARISON = auto()
    """Alternative intervention or control condition."""

    OUTCOME = auto()
    """Results or effects being measured or observed."""

    METHODOLOGY = auto()
    """Study design and methodological criteria."""

    TIMEFRAME = auto()
    """Temporal limitations and date restrictions."""

    GEOGRAPHIC = auto()
    """Geographic or location-specific limitations."""

    LANGUAGE = auto()
    """Language restrictions and inclusions."""

    PUBLICATION = auto()
    """Publication type and status criteria."""

    @property
    def pico_element(self) -> str | None:
        """Returns corresponding PICO/PICOS framework element.

        Maps block purpose to standard systematic review frameworks
        for search organization.

        Returns:
            str | None: PICO element letter or None if not applicable
        """
        mappings = {
            BlockPurpose.POPULATION: "P",
            BlockPurpose.INTERVENTION: "I",
            BlockPurpose.COMPARISON: "C",
            BlockPurpose.OUTCOME: "O",
            BlockPurpose.METHODOLOGY: "S",
            BlockPurpose.TIMEFRAME: None,
            BlockPurpose.GEOGRAPHIC: None,
            BlockPurpose.LANGUAGE: None,
            BlockPurpose.PUBLICATION: None,
        }
        return mappings[self]

    @property
    def required_elements(self) -> list[str]:
        """Returns required components for this block type.

        Specifies elements that must be included for the block
        to be considered complete.

        Returns:
            list[str]: Required elements for this block type
        """
        elements = {
            BlockPurpose.POPULATION: [
                "condition/disease terms",
                "population characteristics",
                "age groups if relevant",
            ],
            BlockPurpose.INTERVENTION: [
                "intervention name",
                "delivery method",
                "common variants",
            ],
            BlockPurpose.COMPARISON: [
                "control condition",
                "alternative interventions",
                "placebo terms if relevant",
            ],
            BlockPurpose.OUTCOME: [
                "primary outcomes",
                "measurement methods",
                "timing if relevant",
            ],
            BlockPurpose.METHODOLOGY: [
                "study design terms",
                "methodology filters",
                "quality indicators",
            ],
            BlockPurpose.TIMEFRAME: ["date range", "date field specification"],
            BlockPurpose.GEOGRAPHIC: [
                "region terms",
                "country names",
                "geographic qualifiers",
            ],
            BlockPurpose.LANGUAGE: [
                "language restrictions",
                "language field specification",
            ],
            BlockPurpose.PUBLICATION: [
                "publication types",
                "publication status",
                "peer review status",
            ],
        }
        return elements[self]

    @property
    def recommended_fields(self) -> dict[str, list[str]]:
        """Returns recommended search fields by database.

        Specifies which database fields should be searched for
        this block type.

        Returns:
            dict[str, list[str]]: Database-specific field recommendations
        """
        fields = {
            BlockPurpose.POPULATION: {
                "pubmed": ["mesh", "tiab", "majr"],
                "embase": ["exp", "ti,ab", "major"],
                "cochrane": ["mesh", "ti,ab,kw"],
            },
            BlockPurpose.INTERVENTION: {
                "pubmed": ["mesh", "tiab", "nm"],
                "embase": ["exp", "ti,ab", "drug/"],
                "cochrane": ["mesh", "ti,ab,kw"],
            },
            BlockPurpose.COMPARISON: {
                "pubmed": ["mesh", "tiab"],
                "embase": ["exp", "ti,ab"],
                "cochrane": ["mesh", "ti,ab,kw"],
            },
            BlockPurpose.OUTCOME: {
                "pubmed": ["mesh", "tiab"],
                "embase": ["exp", "ti,ab"],
                "cochrane": ["mesh", "ti,ab,kw"],
            },
            BlockPurpose.METHODOLOGY: {
                "pubmed": ["pt", "mesh", "sb"],
                "embase": ["exp", "major"],
                "cochrane": ["pt", "mesh"],
            },
            BlockPurpose.TIMEFRAME: {
                "pubmed": ["dp"],
                "embase": ["/py"],
                "cochrane": ["year"],
            },
            BlockPurpose.GEOGRAPHIC: {
                "pubmed": ["mesh", "tiab", "ad"],
                "embase": ["exp", "ti,ab"],
                "cochrane": ["mesh", "ti,ab"],
            },
            BlockPurpose.LANGUAGE: {
                "pubmed": ["la"],
                "embase": ["/lim"],
                "cochrane": ["lg"],
            },
            BlockPurpose.PUBLICATION: {
                "pubmed": ["pt", "sb"],
                "embase": ["exp", "/dt"],
                "cochrane": ["pt"],
            },
        }
        return fields[self]

    @property
    def combination_logic(self) -> str:
        """Returns recommended boolean logic for combining terms.

        Provides guidance on how terms within the block and the block
        itself should be combined.

        Returns:
            str: Combination logic recommendation
        """
        logic = {
            BlockPurpose.POPULATION: (
                "OR within block for synonyms and related terms. "
                "AND with other PICO elements."
            ),
            BlockPurpose.INTERVENTION: (
                "OR within block for intervention variants. "
                "AND with population and outcomes."
            ),
            BlockPurpose.COMPARISON: (
                "OR within block for alternative interventions. "
                "Optional AND with main concepts."
            ),
            BlockPurpose.OUTCOME: (
                "OR within block for related outcomes. "
                "AND with population and intervention."
            ),
            BlockPurpose.METHODOLOGY: (
                "OR within methodology types. AND with main search as a filter."
            ),
            BlockPurpose.TIMEFRAME: (
                "Simple date range using database-specific syntax. "
                "Apply as a filter after main search."
            ),
            BlockPurpose.GEOGRAPHIC: (
                "OR for related regions/countries. AND with main search as a filter."
            ),
            BlockPurpose.LANGUAGE: (
                "OR for multiple languages if needed. Apply as a final filter."
            ),
            BlockPurpose.PUBLICATION: (
                "OR for accepted publication types. AND with main search as a filter."
            ),
        }
        return logic[self]

    @property
    def filter_recommendations(self) -> list[FilterRecommendation]:
        """Returns recommendations for filter application.

        Provides guidance on when and how to apply this block
        as a search filter.

        Returns:
            list[FilterRecommendation]: Filter application recommendations
        """
        recommendations = {
            BlockPurpose.POPULATION: [
                {
                    "timing": "early",
                    "required": True,
                    "impact": "core concept",
                    "caution": "Avoid over-specification",
                }
            ],
            BlockPurpose.INTERVENTION: [
                {
                    "timing": "early",
                    "required": True,
                    "impact": "core concept",
                    "caution": "Include delivery variants",
                }
            ],
            BlockPurpose.COMPARISON: [
                {
                    "timing": "optional",
                    "required": False,
                    "impact": "precision",
                    "caution": "May reduce sensitivity",
                }
            ],
            BlockPurpose.OUTCOME: [
                {
                    "timing": "consider carefully",
                    "required": False,
                    "impact": "may miss studies",
                    "caution": "Often poorly reported",
                }
            ],
            BlockPurpose.METHODOLOGY: [
                {
                    "timing": "late",
                    "required": False,
                    "impact": "precision",
                    "validated_filters": [
                        "Cochrane RCT",
                        "SIGN",
                        "BMJ Clinical Evidence",
                    ],
                }
            ],
            BlockPurpose.TIMEFRAME: [
                {
                    "timing": "last",
                    "required": False,
                    "impact": "currency",
                    "considerations": [
                        "Database coverage",
                        "Entry date vs. Publication date",
                        "Delayed indexing",
                    ],
                }
            ],
            BlockPurpose.GEOGRAPHIC: [
                {
                    "timing": "late",
                    "required": False,
                    "impact": "context",
                    "caution": "Consider multi-center studies",
                }
            ],
            BlockPurpose.LANGUAGE: [
                {
                    "timing": "last",
                    "required": False,
                    "impact": "feasibility",
                    "caution": "Language bias",
                    "document_clearly": True,
                }
            ],
            BlockPurpose.PUBLICATION: [
                {
                    "timing": "late",
                    "required": False,
                    "impact": "precision",
                    "validated_filters": [
                        "Systematic review filters",
                        "Methods filters",
                    ],
                }
            ],
        }
        return recommendations[self]

    @property
    def display_name(self) -> str:
        """Returns formatted display name for UI presentation.

        Provides consistent, human-readable names for use in interfaces
        and documentation.

        Returns:
            str: Human-readable block purpose name
        """
        names = {
            BlockPurpose.POPULATION: "Population/Problem",
            BlockPurpose.INTERVENTION: "Intervention/Exposure",
            BlockPurpose.COMPARISON: "Comparison/Control",
            BlockPurpose.OUTCOME: "Outcome",
            BlockPurpose.METHODOLOGY: "Study Design",
            BlockPurpose.TIMEFRAME: "Time Frame",
            BlockPurpose.GEOGRAPHIC: "Geographic Location",
            BlockPurpose.LANGUAGE: "Language",
            BlockPurpose.PUBLICATION: "Publication Type",
        }
        return names[self]

    @property
    def description(self) -> str:
        """Returns detailed description of the block purpose.

        Provides comprehensive explanations suitable for documentation,
        training materials, and contextual help.

        Returns:
            str: Comprehensive explanation suitable for documentation
        """
        descriptions = {
            BlockPurpose.POPULATION: (
                "Defines the population, patient group, or problem being studied. "
                "Should include relevant population characteristics, condition/disease "
                "terms, and any specific inclusion criteria. Core element that usually "
                "cannot be omitted from the search strategy."
            ),
            BlockPurpose.INTERVENTION: (
                "Specifies the intervention, treatment, or exposure being evaluated. "
                "Should include all relevant delivery methods, dosages, and variants. "
                "For observational studies, may describe exposures or risk factors "
                "rather than interventions."
            ),
            BlockPurpose.COMPARISON: (
                "Describes the control condition or alternative intervention for "
                "comparison. May include placebo, standard care, or alternative "
                "treatments. Sometimes combined with intervention block in search "
                "strategy."
            ),
            BlockPurpose.OUTCOME: (
                "Defines the outcomes or effects being measured. Includes primary "
                "and secondary outcomes, measurement methods, and timing. Often "
                "omitted from search strategies due to inconsistent reporting in "
                "abstracts."
            ),
            BlockPurpose.METHODOLOGY: (
                "Specifies study design and methodological criteria. Usually "
                "applied as filters using validated search strategies. Important "
                "for limiting to specific study types while maintaining search "
                "sensitivity."
            ),
            BlockPurpose.TIMEFRAME: (
                "Defines temporal limitations of the search. May reflect publication "
                "dates, study conduct periods, or database entry dates. Important "
                "to consider database-specific date field implementations."
            ),
            BlockPurpose.GEOGRAPHIC: (
                "Specifies geographic or location-based limitations. May include "
                "countries, regions, or settings. Consider implications for "
                "generalizability and multi-center studies."
            ),
            BlockPurpose.LANGUAGE: (
                "Defines language restrictions or inclusions. Should be justified "
                "and documented clearly. Consider implications of language bias "
                "for review findings."
            ),
            BlockPurpose.PUBLICATION: (
                "Specifies publication types and status criteria. May include "
                "peer-review status, grey literature, or specific document types. "
                "Consider impact on publication bias."
            ),
        }
        return descriptions[self]

    @property
    def suggested_order(self) -> int:
        """Returns suggested order in search strategy.

        Provides recommended position for this block in the overall
        search strategy structure.

        Returns:
            int: Recommended order (lower numbers come first)
        """
        orders = {
            BlockPurpose.POPULATION: 1,
            BlockPurpose.INTERVENTION: 2,
            BlockPurpose.COMPARISON: 3,
            BlockPurpose.OUTCOME: 4,
            BlockPurpose.METHODOLOGY: 5,
            BlockPurpose.GEOGRAPHIC: 6,
            BlockPurpose.TIMEFRAME: 7,
            BlockPurpose.PUBLICATION: 8,
            BlockPurpose.LANGUAGE: 9,
        }
        return orders[self]


class SearchStage(StrEnum):
    """Systematic review search strategy development and execution stages.

    Represents the sequential stages in developing, validating, and executing
    a systematic review search strategy. Each stage has specific requirements,
    deliverables, and quality checks.

    Examples:
        >>> strategy = SearchStrategy(stage=SearchStage.SCOPING)
        >>> strategy.stage.required_outputs
        ['Key concepts identified', 'Initial term list', 'Preliminary results count']
        >>> strategy.stage.can_proceed_to(SearchStage.DEVELOPMENT)
        True  # If requirements are met

    See Also:
        `Cochrane Handbook Chapter 4 <https://training.cochrane.org/handbook/current/chapter-04>`_
        `PRESS Guideline <https://doi.org/10.1016/j.jclinepi.2016.01.021>`_
    """

    SCOPING = auto()
    """Initial exploratory searches to define scope and identify key terms."""

    DEVELOPMENT = auto()
    """Formal strategy development including concept blocks and syntax."""

    VALIDATION = auto()
    """Testing and refinement using validation methods."""

    EXECUTION = auto()
    """Full search implementation across all databases."""

    TRANSLATION = auto()
    """Adaptation of search strategy for different databases."""

    UPDATE = auto()
    """Search update for published reviews."""

    DOCUMENTATION = auto()
    """Complete search strategy reporting and methodology documentation."""

    @property
    def required_outputs(self) -> list[str]:
        """Returns required deliverables for this stage.

        Specifies the outputs that must be produced during this
        stage for it to be considered complete.

        Returns:
            list[str]: Required stage outputs
        """
        outputs = {
            SearchStage.SCOPING: [
                "Key concepts identified",
                "Initial term list",
                "Relevant databases identified",
                "Preliminary results estimate",
                "Example relevant papers",
            ],
            SearchStage.DEVELOPMENT: [
                "Complete concept blocks",
                "Controlled vocabulary terms mapped",
                "Field codes specified",
                "Boolean logic structure",
                "Initial strategy draft",
            ],
            SearchStage.VALIDATION: [
                "Validation method documentation",
                "Reference set verification",
                "Peer review feedback",
                "Sensitivity analysis",
                "Precision estimates",
            ],
            SearchStage.EXECUTION: [
                "Complete search results",
                "Results per database",
                "Deduplication report",
                "Search alerts set",
                "Results backup",
            ],
            SearchStage.TRANSLATION: [
                "Database-specific syntax",
                "Platform-specific adaptations",
                "Field code mappings",
                "Operator translations",
                "Coverage analysis",
            ],
            SearchStage.UPDATE: [
                "Update time frame",
                "Modified strategy (if needed)",
                "New results only",
                "Update documentation",
                "Integration plan",
            ],
            SearchStage.DOCUMENTATION: [
                "PRISMA-S checklist",
                "Complete search strategies",
                "Search methodology",
                "Grey literature sources",
                "Search dates and results",
            ],
        }
        return outputs[self]

    @property
    def prerequisites(self) -> list[SearchStage]:
        """Returns prerequisite stages.

        Identifies which stages must be completed before
        this stage can begin.

        Returns:
            list[SearchStage]: Required previous stages
        """
        prereqs = {
            SearchStage.SCOPING: [],
            SearchStage.DEVELOPMENT: [SearchStage.SCOPING],
            SearchStage.VALIDATION: [SearchStage.DEVELOPMENT],
            SearchStage.EXECUTION: [SearchStage.VALIDATION],
            SearchStage.TRANSLATION: [SearchStage.DEVELOPMENT],
            SearchStage.UPDATE: [SearchStage.DOCUMENTATION],
            SearchStage.DOCUMENTATION: [SearchStage.EXECUTION],
        }
        return prereqs[self]

    @property
    def validation_checks(self) -> list[str]:
        """Returns validation requirements for this stage.

        Specifies checks that should be performed to ensure
        stage quality and completeness.

        Returns:
            list[str]: Required validation checks
        """
        checks = {
            SearchStage.SCOPING: [
                "Key concepts cover research question",
                "Initial results seem relevant",
                "Major databases identified",
                "Resource requirements estimated",
                "Timeline feasibility assessed",
            ],
            SearchStage.DEVELOPMENT: [
                "All PICO elements covered",
                "Controlled vocabulary used appropriately",
                "Field codes correct for database",
                "Boolean logic validates",
                "No syntax errors present",
            ],
            SearchStage.VALIDATION: [
                "Retrieves known relevant papers",
                "Reasonable precision observed",
                "Peer review completed",
                "Subject expert consulted",
                "Search filters validated",
            ],
            SearchStage.EXECUTION: [
                "All planned databases searched",
                "Results successfully exported",
                "Deduplication completed",
                "Results archived securely",
                "Search dates recorded",
            ],
            SearchStage.TRANSLATION: [
                "Syntax valid for each database",
                "Equivalent concepts maintained",
                "Field mappings verified",
                "Results reasonable across databases",
                "Coverage gaps identified",
            ],
            SearchStage.UPDATE: [
                "Original strategy still valid",
                "New terms considered",
                "Date limits correct",
                "Results deduplicated against original",
                "Changes documented",
            ],
            SearchStage.DOCUMENTATION: [
                "PRISMA-S compliant",
                "All strategies included",
                "Dates and databases listed",
                "Limits documented",
                "Results counts reported",
            ],
        }
        return checks[self]

    @property
    def stakeholders(self) -> list[str]:
        """Returns stakeholders involved in this stage.

        Identifies roles and expertise needed for successful
        stage completion.

        Returns:
            list[str]: Required stakeholders
        """
        roles = {
            SearchStage.SCOPING: [
                "Information specialist",
                "Subject expert",
                "Review lead",
                "Project manager",
            ],
            SearchStage.DEVELOPMENT: [
                "Information specialist",
                "Database expert",
                "Subject expert",
                "Review methodologist",
            ],
            SearchStage.VALIDATION: [
                "Information specialist",
                "Peer reviewer",
                "Subject expert",
                "Statistician",
            ],
            SearchStage.EXECUTION: [
                "Information specialist",
                "Data manager",
                "Review team members",
            ],
            SearchStage.TRANSLATION: [
                "Information specialist",
                "Database experts",
                "Language specialists",
            ],
            SearchStage.UPDATE: [
                "Information specialist",
                "Original review team",
                "Subject expert",
            ],
            SearchStage.DOCUMENTATION: [
                "Information specialist",
                "Review methodologist",
                "Project manager",
            ],
        }
        return roles[self]

    @property
    def typical_duration(self) -> str:
        """Returns typical time required for stage completion.

        Provides estimated duration ranges based on common
        practice and complexity.

        Returns:
            str: Typical duration estimate
        """
        durations: dict[SearchStage, str] = {
            SearchStage.SCOPING: "2-5 days",
            SearchStage.DEVELOPMENT: "1-3 weeks",
            SearchStage.VALIDATION: "1-2 weeks",
            SearchStage.EXECUTION: "3-5 days",
            SearchStage.TRANSLATION: "3-7 days",
            SearchStage.UPDATE: "1-2 weeks",
            SearchStage.DOCUMENTATION: "2-4 days",
        }
        return durations[self]

    @property
    def common_challenges(self) -> list[str]:  # pyright: ignore [ReportUnknownParameterType]
        """Returns common challenges and pitfalls.

        Identifies typical issues and challenges encountered
        during this stage.

        Returns:
            list[str]: Common challenges and mitigations
        """
        challenges: dict[SearchStage, list[str]] = {
            SearchStage.SCOPING: [
                "Scope too broad or narrow",
                "Missing key concepts",
                "Resource underestimation",
                "Inadequate expert input",
                "Poor feasibility assessment",
            ],
            SearchStage.DEVELOPMENT: [
                "Missed controlled vocabulary terms",
                "Incorrect field codes",
                "Complex Boolean logic errors",
                "Inadequate synonyms",
                "Platform-specific syntax issues",
            ],
            SearchStage.VALIDATION: [
                "Incomplete reference sets",
                "Poor precision assessment",
                "Limited peer review",
                "Inadequate testing",
                "Missing edge cases",
            ],
            SearchStage.EXECUTION: [
                "Database access issues",
                "Export limitations",
                "Deduplication errors",
                "Incomplete documentation",
                "Results management problems",
            ],
            SearchStage.TRANSLATION: [
                "Vocabulary differences",
                "Syntax incompatibilities",
                "Missing field equivalents",
                "Coverage gaps",
                "Resource limitations",
            ],
            SearchStage.UPDATE: [
                "Changed database interfaces",
                "New terminology",
                "Modified indexing",
                "Integration challenges",
                "Incomplete documentation",
            ],
            SearchStage.DOCUMENTATION: [
                "Missing details",
                "Inconsistent reporting",
                "Inadequate methodology description",
                "Poor reproducibility",
                "Incomplete PRISMA-S compliance",
            ],
        }
        return challenges[self]

    @property
    def quality_metrics(self) -> dict[str, str]:
        """Returns quality assessment criteria.

        Provides metrics and criteria for assessing the
        quality of stage completion.

        Returns:
            dict[str, str]: Quality metrics and standards
        """
        metrics = {
            SearchStage.SCOPING: {
                "concept_coverage": "All key concepts identified",
                "database_selection": "Appropriate databases selected",
                "feasibility": "Resource requirements realistic",
                "relevance": "Initial results appropriate",
                "completeness": "Major sources covered",
            },
            SearchStage.DEVELOPMENT: {
                "vocabulary_usage": "Controlled terms properly used",
                "syntax_validity": "No syntax errors present",
                "logic_structure": "Boolean logic appropriate",
                "field_accuracy": "Field codes correctly applied",
                "completeness": "All concepts covered",
            },
            SearchStage.VALIDATION: {
                "reference_retrieval": "Known papers retrieved",
                "precision_rate": "Acceptable precision shown",
                "peer_review": "Expert review completed",
                "sensitivity": "High recall demonstrated",
                "documentation": "Methods fully documented",
            },
            SearchStage.EXECUTION: {
                "completion": "All databases searched",
                "export_success": "Results properly exported",
                "deduplication": "Duplicates properly handled",
                "archiving": "Results securely stored",
                "documentation": "Process fully documented",
            },
            SearchStage.TRANSLATION: {
                "syntax_accuracy": "Correct database syntax",
                "concept_equivalence": "Concepts properly mapped",
                "field_mapping": "Fields correctly translated",
                "coverage": "Database coverage analyzed",
                "validation": "Results verified",
            },
            SearchStage.UPDATE: {
                "currency": "Search up to date",
                "compatibility": "Strategy still appropriate",
                "documentation": "Changes documented",
                "integration": "Results properly merged",
                "validation": "Update validated",
            },
            SearchStage.DOCUMENTATION: {
                "completeness": "All elements reported",
                "clarity": "Clear methodology description",
                "reproducibility": "Sufficient detail provided",
                "standards": "PRISMA-S compliant",
                "accuracy": "Information verified",
            },
        }
        return metrics[self]


class ValidationMethod(StrEnum):
    """Methods for validating systematic review search strategies.

    These methods ensure search strategy quality, comprehensiveness,
    and reproducibility. Each method targets specific aspects of
    search strategy validation.

    Examples:
        >>> validation = SearchValidation(method=ValidationMethod.REFERENCE_SET)
        >>> print(validation.method.requirements)
        ['Known relevant papers', 'Citation details', 'Retrieval verification']
        >>> validation.method.is_suitable_for(strategy_type="intervention")
        True

    See Also:
        `PRESS Guideline <https://doi.org/10.1016/j.jclinepi.2016.01.021>`_
        `Cochrane Handbook Ch 4.4.7 <https://training.cochrane.org/handbook/current/chapter-04-4>`_
    """

    REFERENCE_SET = auto()
    """Known relevant articles checking against search results."""

    PEER_REVIEW = auto()
    """Expert review using structured assessment tools."""

    TRANSLATION = auto()
    """Cross-database translation and syntax verification."""

    CITATION_TRACKING = auto()
    """Forward and backward citation analysis."""

    SYNTAX = auto()
    """Technical syntax and operator validation."""

    TEXT_ANALYSIS = auto()
    """Analysis of search result relevance through text mining."""

    PRECISION_TEST = auto()
    """Assessment of result set precision through sampling."""

    @property
    def requirements(self) -> list[str]:
        """Returns requirements for implementing this validation method.

        Specifies resources, expertise, and prerequisites needed
        to apply this validation method.

        Returns:
            list[str]: Method requirements
        """
        reqs = {
            ValidationMethod.REFERENCE_SET: [
                "Set of known relevant papers",
                "Complete citation details",
                "Database coverage verification",
                "Result matching protocol",
                "Documentation template",
            ],
            ValidationMethod.PEER_REVIEW: [
                "Qualified peer reviewer",
                "PRESS checklist",
                "Complete search documentation",
                "Review feedback format",
                "Resolution process",
            ],
            ValidationMethod.TRANSLATION: [
                "Database-specific syntax guides",
                "Field code mappings",
                "Platform documentation",
                "Equivalent term sets",
                "Cross-platform expertise",
            ],
            ValidationMethod.CITATION_TRACKING: [
                "Citation database access",
                "Seed article set",
                "Citation extraction tools",
                "Analysis protocol",
                "Documentation framework",
            ],
            ValidationMethod.SYNTAX: [
                "Database syntax guides",
                "Operator rules documentation",
                "Testing protocol",
                "Error logging system",
                "Validation checklist",
            ],
            ValidationMethod.TEXT_ANALYSIS: [
                "Text analysis tools",
                "Sample result set",
                "Analysis protocol",
                "Term frequency analysis",
                "Relevance criteria",
            ],
            ValidationMethod.PRECISION_TEST: [
                "Sampling protocol",
                "Relevance criteria",
                "Assessment form",
                "Statistical methods",
                "Documentation template",
            ],
        }
        return reqs[self]

    @property
    def validation_steps(self) -> list[str]:
        """Returns step-by-step validation procedure.

        Provides ordered sequence of steps for implementing
        this validation method.

        Returns:
            list[str]: Implementation steps
        """
        steps = {
            ValidationMethod.REFERENCE_SET: [
                "1. Compile known relevant papers",
                "2. Verify database coverage",
                "3. Execute search strategy",
                "4. Match results against reference set",
                "5. Analyze missing items",
                "6. Adjust strategy if needed",
                "7. Document retrieval rate",
            ],
            ValidationMethod.PEER_REVIEW: [
                "1. Select qualified reviewer",
                "2. Provide complete strategy",
                "3. Apply PRESS checklist",
                "4. Review search elements",
                "5. Provide written feedback",
                "6. Discuss recommendations",
                "7. Document changes made",
            ],
            ValidationMethod.TRANSLATION: [
                "1. Identify target databases",
                "2. Map field codes",
                "3. Translate operators",
                "4. Adapt syntax",
                "5. Test translations",
                "6. Compare results",
                "7. Document equivalence",
            ],
            ValidationMethod.CITATION_TRACKING: [
                "1. Identify seed articles",
                "2. Extract citations",
                "3. Analyze citation patterns",
                "4. Identify missing papers",
                "5. Assess importance",
                "6. Update strategy",
                "7. Document process",
            ],
            ValidationMethod.SYNTAX: [
                "1. Review operator usage",
                "2. Check field codes",
                "3. Verify nesting",
                "4. Test truncation",
                "5. Validate proximity",
                "6. Check line breaks",
                "7. Document checks",
            ],
            ValidationMethod.TEXT_ANALYSIS: [
                "1. Extract result set",
                "2. Analyze term frequency",
                "3. Identify patterns",
                "4. Assess relevance",
                "5. Review outliers",
                "6. Adjust strategy",
                "7. Document findings",
            ],
            ValidationMethod.PRECISION_TEST: [
                "1. Define sample size",
                "2. Random sample selection",
                "3. Apply inclusion criteria",
                "4. Calculate precision",
                "5. Analyze irrelevant hits",
                "6. Adjust strategy",
                "7. Document results",
            ],
        }
        return steps[self]

    @property
    def quality_indicators(self) -> dict[str, str]:
        """Returns quality assessment criteria.

        Provides metrics and benchmarks for assessing the
        quality of validation implementation.

        Returns:
            dict[str, str]: Quality indicators and standards
        """
        indicators = {
            ValidationMethod.REFERENCE_SET: {
                "retrieval_rate": "≥90% of reference set retrieved",
                "coverage": "All key papers available in database",
                "documentation": "Missing items explained",
                "adjustments": "Strategy modifications logged",
                "completeness": "All steps documented",
            },
            ValidationMethod.PEER_REVIEW: {
                "reviewer_qualification": "Subject and search expertise",
                "checklist_completion": "All PRESS elements addressed",
                "feedback_quality": "Specific and actionable",
                "response": "All points addressed",
                "documentation": "Process fully documented",
            },
            ValidationMethod.TRANSLATION: {
                "syntax_accuracy": "No technical errors",
                "concept_equivalence": "Meaning preserved",
                "field_mapping": "Appropriate translations",
                "result_comparability": "Similar result patterns",
                "documentation": "Differences explained",
            },
            ValidationMethod.CITATION_TRACKING: {
                "seed_quality": "Key papers included",
                "citation_coverage": "Major citations found",
                "analysis_depth": "Multiple generations checked",
                "documentation": "Process reproducible",
                "strategy_updates": "Changes incorporated",
            },
            ValidationMethod.SYNTAX: {
                "operator_validity": "All operators correct",
                "field_accuracy": "Fields properly specified",
                "nesting_logic": "Parentheses balanced",
                "truncation": "Wildcards properly used",
                "documentation": "All checks recorded",
            },
            ValidationMethod.TEXT_ANALYSIS: {
                "sample_size": "Adequate sample analyzed",
                "term_patterns": "Clear term relationships",
                "relevance_rate": "High relevant content",
                "outlier_analysis": "Exceptions explained",
                "documentation": "Methods described",
            },
            ValidationMethod.PRECISION_TEST: {
                "sample_size": "Statistically valid sample",
                "assessment_quality": "Reliable relevance judging",
                "precision_rate": "Acceptable precision shown",
                "analysis": "Irrelevant hits examined",
                "documentation": "Process reproducible",
            },
        }
        return indicators[self]

    @property
    def suitable_for(self) -> list[str]:
        """Returns review types suitable for this method.

        Identifies systematic review types where this validation
        method is most appropriate.

        Returns:
            list[str]: Suitable review types
        """
        suitability = {
            ValidationMethod.REFERENCE_SET: [
                "Intervention reviews",
                "Clinical questions",
                "Well-established topics",
                "Updates of existing reviews",
                "Methods reviews",
            ],
            ValidationMethod.PEER_REVIEW: [
                "All review types",
                "Complex searches",
                "Novel topics",
                "High-stakes reviews",
                "Methodology reviews",
            ],
            ValidationMethod.TRANSLATION: [
                "Multi-database searches",
                "International reviews",
                "Platform-specific searches",
                "Complex syntax",
                "Multiple language searches",
            ],
            ValidationMethod.CITATION_TRACKING: [
                "Methodology reviews",
                "Theory development",
                "Historical topics",
                "Author-focused reviews",
                "Research networks",
            ],
            ValidationMethod.SYNTAX: [
                "Complex Boolean logic",
                "Multi-line strategies",
                "Proximity searching",
                "Field-intensive searches",
                "Platform migrations",
            ],
            ValidationMethod.TEXT_ANALYSIS: [
                "New research areas",
                "Terminology mapping",
                "Concept development",
                "Scoping reviews",
                "Search refinement",
            ],
            ValidationMethod.PRECISION_TEST: [
                "Large result sets",
                "New search filters",
                "Methodology validation",
                "Resource-intensive reviews",
                "Search optimization",
            ],
        }
        return suitability[self]

    @property
    def limitations(self) -> list[str]:
        """Returns method limitations and considerations.

        Identifies potential drawbacks and limitations of
        this validation method.

        Returns:
            list[str]: Method limitations
        """
        limits = {
            ValidationMethod.REFERENCE_SET: [
                "Only validates known items",
                "May miss novel relevant papers",
                "Depends on reference set quality",
                "Time-consuming for large sets",
                "Database coverage dependent",
            ],
            ValidationMethod.PEER_REVIEW: [
                "Reviewer expertise dependent",
                "Subjective elements",
                "Resource intensive",
                "May delay completion",
                "Reviewer availability",
            ],
            ValidationMethod.TRANSLATION: [
                "Platform-specific constraints",
                "Perfect equivalence rare",
                "Requires multiple expertise",
                "Time-consuming",
                "May need compromises",
            ],
            ValidationMethod.CITATION_TRACKING: [
                "Citation lag time",
                "Database coverage gaps",
                "Resource intensive",
                "May miss recent papers",
                "Network completeness unknown",
            ],
            ValidationMethod.SYNTAX: [
                "Technical focus only",
                "Misses conceptual issues",
                "Platform dependent",
                "Time-consuming",
                "Requires technical expertise",
            ],
            ValidationMethod.TEXT_ANALYSIS: [
                "Tool availability",
                "Technical complexity",
                "Resource intensive",
                "May miss context",
                "Requires analysis expertise",
            ],
            ValidationMethod.PRECISION_TEST: [
                "Sample size limitations",
                "Resource intensive",
                "Subject expertise needed",
                "Statistical complexity",
                "May need larger samples",
            ],
        }
        return limits[self]

    @property
    def documentation_requirements(self) -> list[str]:
        """Returns documentation requirements.

        Specifies what should be documented when using
        this validation method.

        Returns:
            list[str]: Required documentation elements
        """
        docs = {
            ValidationMethod.REFERENCE_SET: [
                "Reference set composition",
                "Database coverage analysis",
                "Retrieval rates",
                "Missing item analysis",
                "Strategy adjustments",
                "Final performance metrics",
            ],
            ValidationMethod.PEER_REVIEW: [
                "Reviewer qualifications",
                "PRESS checklist results",
                "Reviewer feedback",
                "Response to feedback",
                "Changes implemented",
                "Resolution process",
            ],
            ValidationMethod.TRANSLATION: [
                "Original strategy",
                "Translation decisions",
                "Field mappings",
                "Syntax adaptations",
                "Results comparison",
                "Platform differences",
            ],
            ValidationMethod.CITATION_TRACKING: [
                "Seed article selection",
                "Citation extraction method",
                "Network analysis",
                "New articles found",
                "Strategy updates",
                "Impact assessment",
            ],
            ValidationMethod.SYNTAX: [
                "Validation checklist",
                "Error log",
                "Corrections made",
                "Testing protocol",
                "Final syntax",
                "Platform details",
            ],
            ValidationMethod.TEXT_ANALYSIS: [
                "Analysis method",
                "Sample characteristics",
                "Term patterns",
                "Relevance criteria",
                "Strategy adjustments",
                "Result impact",
            ],
            ValidationMethod.PRECISION_TEST: [
                "Sampling method",
                "Assessment criteria",
                "Precision calculations",
                "Error analysis",
                "Strategy adjustments",
                "Final precision rate",
            ],
        }
        return docs[self]


class SearchPrecision(StrEnum):
    """Defines precision-recall balance in systematic review searches.

    Represents different approaches to balancing search precision (specificity)
    and recall (sensitivity) in systematic review search strategies. Each level
    has implications for resource requirements, time frames, and completeness.

    Examples:
        >>> strategy = SearchStrategy(precision=SearchPrecision.BALANCED)
        >>> print(strategy.precision.expected_noise_ratio)
        '40-60% irrelevant results'
        >>> strategy.precision.suitable_for_review_type("rapid_review")
        True

    See Also:
        `Cochrane Handbook Ch 4.4.4 <https://training.cochrane.org/handbook/current/chapter-04-4>`_
        `JBI Manual Ch 3.2.4 <https://jbi-global-wiki.refined.site/space/MANUAL/4688722/3.2.4++Search+strategy>`_
    """

    HIGHLY_PRECISE = auto()
    """Maximum precision approach prioritizing result set relevance."""

    BALANCED = auto()
    """Balanced approach between precision and recall."""

    HIGHLY_SENSITIVE = auto()
    """Maximum sensitivity approach prioritizing comprehensive retrieval."""

    RAPID = auto()
    """Pragmatic approach for rapid or scoping reviews."""

    COMPREHENSIVE = auto()
    """Full systematic approach with extensive searching."""

    @property
    def expected_noise_ratio(self) -> str:
        """Returns expected proportion of irrelevant results.

        Provides guidance on anticipated noise levels in
        search results.

        Returns:
            str: Expected noise level description
        """
        ratios = {
            SearchPrecision.HIGHLY_PRECISE: "10-30% irrelevant results",
            SearchPrecision.BALANCED: "40-60% irrelevant results",
            SearchPrecision.HIGHLY_SENSITIVE: "70-90% irrelevant results",
            SearchPrecision.RAPID: "30-50% irrelevant results",
            SearchPrecision.COMPREHENSIVE: "60-80% irrelevant results",
        }
        return ratios[self]

    @property
    def search_techniques(self) -> list[str]:
        """Returns recommended search techniques.

        Lists search approaches and techniques appropriate
        for this precision level.

        Returns:
            list[str]: Recommended techniques
        """
        techniques = {
            SearchPrecision.HIGHLY_PRECISE: [
                "Focused controlled vocabulary",
                "Major subject headings only",
                "Precise phrase searching",
                "Field-restricted searching",
                "Concept coordination",
            ],
            SearchPrecision.BALANCED: [
                "Mixed controlled/free text",
                "Selective truncation",
                "Selected synonyms",
                "Some field restrictions",
                "Core concept combinations",
            ],
            SearchPrecision.HIGHLY_SENSITIVE: [
                "Extensive synonyms",
                "Broad truncation",
                "Multiple concept variants",
                "Minimal field restrictions",
                "Broad controlled vocabulary",
            ],
            SearchPrecision.RAPID: [
                "Key controlled terms",
                "Limited synonyms",
                "Strategic field limits",
                "Focus on major concepts",
                "Pragmatic combinations",
            ],
            SearchPrecision.COMPREHENSIVE: [
                "Extensive vocabulary",
                "Multiple approaches",
                "Supplementary searching",
                "Citation tracking",
                "Grey literature",
            ],
        }
        return techniques[self]

    @property
    def resource_implications(self) -> dict[str, str]:
        """Returns resource requirement implications.

        Describes resource needs and implications for
        different aspects of the review.

        Returns:
            dict[str, str]: Resource implications
        """
        implications = {
            SearchPrecision.HIGHLY_PRECISE: {
                "time": "Moderate search development, faster screening",
                "expertise": "High subject expertise needed",
                "staff": "Smaller screening team possible",
                "cost": "Lower screening costs",
                "risk": "May miss relevant studies",
            },
            SearchPrecision.BALANCED: {
                "time": "Moderate for all phases",
                "expertise": "Mixed expertise team",
                "staff": "Average team size",
                "cost": "Moderate overall costs",
                "risk": "Acceptable evidence coverage",
            },
            SearchPrecision.HIGHLY_SENSITIVE: {
                "time": "Quick search, extensive screening",
                "expertise": "High search expertise needed",
                "staff": "Large screening team required",
                "cost": "High screening costs",
                "risk": "Risk of information overload",
            },
            SearchPrecision.RAPID: {
                "time": "Shortened timelines",
                "expertise": "Experienced rapid review team",
                "staff": "Small focused team",
                "cost": "Lower overall costs",
                "risk": "Acknowledged evidence gaps",
            },
            SearchPrecision.COMPREHENSIVE: {
                "time": "Extended timelines",
                "expertise": "Multiple expert types needed",
                "staff": "Large diverse team",
                "cost": "High overall costs",
                "risk": "Resource intensive",
            },
        }
        return implications[self]

    @property
    def suitable_review_types(self) -> list[str]:
        """Returns suitable systematic review types.

        Lists review types where this precision level
        is most appropriate.

        Returns:
            list[str]: Suitable review types
        """
        types = {
            SearchPrecision.HIGHLY_PRECISE: [
                "Technology assessments",
                "Clinical practice guidelines",
                "Focused clinical questions",
                "Update reviews",
                "Resource-limited reviews",
            ],
            SearchPrecision.BALANCED: [
                "Standard systematic reviews",
                "Intervention reviews",
                "Mixed-methods reviews",
                "Review updates",
                "Clinical questions",
            ],
            SearchPrecision.HIGHLY_SENSITIVE: [
                "Safety reviews",
                "Adverse effects",
                "New interventions",
                "Complex interventions",
                "Methods reviews",
            ],
            SearchPrecision.RAPID: [
                "Rapid reviews",
                "Scoping reviews",
                "Policy briefs",
                "Emergency responses",
                "Decision support",
            ],
            SearchPrecision.COMPREHENSIVE: [
                "Cochrane reviews",
                "Guidelines development",
                "Regulatory submissions",
                "HTA reports",
                "Complex interventions",
            ],
        }
        return types[self]

    @property
    def validation_requirements(self) -> list[str]:
        """Returns validation requirements.

        Specifies validation approaches appropriate for
        this precision level.

        Returns:
            list[str]: Required validation steps
        """
        validation = {
            SearchPrecision.HIGHLY_PRECISE: [
                "Precision testing",
                "Known item searching",
                "Subject expert review",
                "Term relevance check",
                "Results assessment",
            ],
            SearchPrecision.BALANCED: [
                "Reference checking",
                "Peer review",
                "Sample screening",
                "Strategy review",
                "Citation checking",
            ],
            SearchPrecision.HIGHLY_SENSITIVE: [
                "Comprehensive checking",
                "Multiple validation methods",
                "Sensitivity analysis",
                "Search extensions",
                "Gap analysis",
            ],
            SearchPrecision.RAPID: [
                "Focused validation",
                "Key reference checking",
                "Expert consultation",
                "Quick assessment",
                "Limitation documentation",
            ],
            SearchPrecision.COMPREHENSIVE: [
                "Multiple validation methods",
                "Extensive testing",
                "External review",
                "Supplementary searching",
                "Documentation review",
            ],
        }
        return validation[self]

    @property
    def adjustment_strategies(self) -> list[str]:
        """Returns strategies for precision adjustment.

        Provides approaches for adjusting search precision
        while maintaining quality.

        Returns:
            list[str]: Adjustment strategies
        """
        strategies = {
            SearchPrecision.HIGHLY_PRECISE: [
                "Add concept coordination",
                "Restrict to major headings",
                "Use proximity operators",
                "Limit free text",
                "Focus field choices",
            ],
            SearchPrecision.BALANCED: [
                "Selective concept combination",
                "Mixed vocabulary approach",
                "Strategic truncation",
                "Selected field limits",
                "Key phrase searching",
            ],
            SearchPrecision.HIGHLY_SENSITIVE: [
                "Expand vocabulary",
                "Add synonyms",
                "Broaden truncation",
                "Reduce restrictions",
                "Include variants",
            ],
            SearchPrecision.RAPID: [
                "Focus on key concepts",
                "Use validated filters",
                "Limit databases",
                "Structured approach",
                "Strategic limits",
            ],
            SearchPrecision.COMPREHENSIVE: [
                "Multiple approaches",
                "Supplementary methods",
                "Iterative development",
                "Expert input",
                "Broad scope",
            ],
        }
        return strategies[self]

    @property
    def documentation_needs(self) -> list[str]:
        """Returns documentation requirements.

        Specifies documentation needed to support and
        justify the precision approach.

        Returns:
            list[str]: Required documentation
        """
        docs = {
            SearchPrecision.HIGHLY_PRECISE: [
                "Precision rationale",
                "Term selection criteria",
                "Coordination decisions",
                "Precision testing results",
                "Known item verification",
            ],
            SearchPrecision.BALANCED: [
                "Approach justification",
                "Term decisions",
                "Balance assessment",
                "Validation results",
                "Adjustment rationale",
            ],
            SearchPrecision.HIGHLY_SENSITIVE: [
                "Sensitivity rationale",
                "Coverage decisions",
                "Validation methods",
                "Resource implications",
                "Comprehensiveness evidence",
            ],
            SearchPrecision.RAPID: [
                "Methodology statement",
                "Approach limitations",
                "Key decisions",
                "Timeline constraints",
                "Validation steps",
            ],
            SearchPrecision.COMPREHENSIVE: [
                "Full methodology",
                "Approach justification",
                "Multiple validations",
                "Resource allocation",
                "Supplementary methods",
            ],
        }
        return docs[self]


class CriteriaFramework(StrEnum):
    """Inclusion criteria framework type.

    Todo:
        - Gen descriptions, questions, etc. as properties

    Attributes:
        ECLIPSE (str): ECLIPSE
        PEO (str): PEO
        PICO (str): PICO
        PICOS (str): PICOS
        PICOT (str): PICOT
        PICOS_T (str): PICOS/T
        SPIDER (str): SPIDER
        SPICE (str): SPICE
    """

    def __new__(cls, value: str) -> t.Self:  # noqa: D102 (missing docstring)
        self = str.__new__(cls, value)
        self._value_ = value.upper()
        if value == "picos_t":
            self._value_ = "PICOS/T"
        return self

    ECLIPSE = auto()
    PEO = auto()
    PICO = auto()
    PICOS = auto()
    PICOT = auto()
    PICOS_T = auto()
    SPIDER = auto()
    SPICE = auto()


"""Exclusion categories."""

type ComparisonExclusionReason = Literal[
    "Inappropriate control group",
    "Missing baseline data",
    "Incorrect comparator",
    "Inadequate randomization method",
    "Insufficient blinding procedure",
    "Inappropriate crossover design",
]

type InterventionExclusionReason = Literal[
    "Intervention timing does not match criteria",
    "Dosage outside specified range",
    "Incorrect delivery or administration method",
    "Protocol deviation from inclusion criteria",
    "Excluded intervention combination",
    "Intervention duration outside criteria",
]

type OutcomeExclusionReason = Literal[
    "Invalid outcome measurement method",
    "Incorrect measurement timepoint",
    "Inappropriate outcome metric",
    "Incomplete outcome reporting",
    "Invalid surrogate endpoint",
    "Insufficient follow-up period",
]

type PopulationExclusionReason = Literal[
    "Wrong age range for inclusion criteria",
    "Non-human subjects",
    "Condition or disease mismatch",
    "Excluded comorbidity present",
    "Demographics outside criteria",
    "Inappropriate study setting",
]

type ReportingExclusionReason = Literal[
    "Non-included language",
    "Duplicate publication",
    "Outside date range",
    "Not peer-reviewed",
    "Retracted publication",
    "Pre-print publication",
]


type StudyDesignExclusionReason = Literal[
    "Wrong study design type",
    "Sample size below requirement",
    "Study duration too short",
    "Ethical concerns identified",
    "Major protocol violations",
    "Study not pre-registered",
]


class ScreeningStrategyType(StrEnum):
    """Maps to the type of prompt used. See app/agents.py comments."""

    CONSERVATIVE = auto()
    COMPREHENSIVE = auto()


class LogLevel(StrEnum):
    """Loguru log levels.

    Attributes:
        TRACE | trace (str|int): TRACE | 10
        DEBUG | debug (str|int): DEBUG | 20
        INFO | info (str|int): INFO | 30
        SUCCESS | success (str|int): SUCCESS | 25
        WARNING | warning (str|int): WARNING | 30
        ERROR | error (str|int): ERROR | 40
        CRITICAL | critical (str|int): CRITICAL | 50

    Examples:
        >>> LogLevel.INFO.int
        ... 30
        >>> list(LogLevel.__members__)
        ... ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    """

    def __new__(cls, value: str, level_int: int, *args: t.Any) -> t.Self:
        self = str.__new__(cls, value.upper())
        self._value_ = value.upper()
        self.int = level_int
        return self

    def __init__(self, *args: t.Any) -> None:
        self.__class__.to_list = list(self.__class__.__members__)

    TRACE = auto(), 10
    DEBUG = auto(), 20
    INFO = auto(), 30
    SUCCESS = auto(), 25
    WARNING = auto(), 30
    ERROR = auto(), 40
    CRITICAL = auto(), 50
