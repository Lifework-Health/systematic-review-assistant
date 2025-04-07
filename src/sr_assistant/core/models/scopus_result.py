from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ScopusResult(BaseModel):
    """Scopus search result model."""
    
    id: UUID
    review_id: UUID
    scopus_id: str
    title: str
    abstract: str
    authors: str
    year: int
    journal: str
    doi: str
    created_at: datetime
    updated_at: datetime 