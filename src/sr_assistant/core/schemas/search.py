"""Schemas related to search strategy bounded context of systematic reviews.

See Also:
    - Enum types in :mod:`core.types.search`
    - Enum types in  :mod:`core.types.citations`
    - Database models in :mod:`core.models.search`
    - Events and commands are work in progress.
"""

from __future__ import annotations

from enum import StrEnum, auto
from typing import Annotated

from pydantic import BaseModel, Field


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


class SearchField(BaseModel):
    """Represents a searchable field in a database with platform-specific details.

    Search fields vary by database and platform, with the same conceptual field
    potentially having different syntax across platforms.

    Examples:
        Title field syntax variations:
            * PubMed: cancer[ti]
            * Ovid: cancer.ti
            * EBSCO: TI cancer

    Note:
        Field behavior may vary across platforms even when syntax is similar.

    See Also:
        :class:`FieldType`: For field type classification details.
        :class:`DatabasePlatform`: For platform-specific information.
    """

    code: Annotated[
        str,
        Field(
            description="Field code used in search syntax",
            examples=["[ti]", ".ti", "TI"],
            title="Field Code",
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Human-readable field name",
            examples=["Title", "Abstract", "MeSH Terms"],
            title="Field Name",
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Detailed description of the field's purpose and usage",
            examples=["Search within article titles only"],
            title="Field Description",
        ),
    ]
    field_type: Annotated[
        FieldType,
        Field(
            description="Classification of the field type for cross-database mapping",
            title="Field Type",
        ),
    ]
    is_controlled_vocabulary: Annotated[
        bool,
        Field(
            default=False,
            description="Indicates if the field uses a controlled vocabulary (e.g., MeSH, Emtree)",
            title="Is Controlled Vocabulary",
        ),
    ]
    platforms: Annotated[
        set[DatabasePlatform],
        Field(
            default_factory=lambda: {DatabasePlatform.NATIVE},
            description="Platforms where this field code is valid",
            title="Valid Platforms",
        ),
    ]
    syntax_examples: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="Examples of valid syntax for this field",
            examples=["cancer[ti]", "neoplasm*[ti]"],
            title="Syntax Examples",
        ),
    ]

    model_config: ConfigDict = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "[ti]",
                    "name": "Title",
                    "description": "Search within article titles only",
                    "field_type": "title",
                    "is_controlled_vocabulary": False,
                    "platforms": ["native"],
                    "syntax_examples": ["cancer[ti]", "neoplasm*[ti]"],
                }
            ]
        }
    }
