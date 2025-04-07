from __future__ import annotations

import typing as t
from datetime import datetime
from uuid import UUID

from elsapy.elsclient import ElsClient
from elsapy.elssearch import ElsSearch
from loguru import logger
from pydantic import BaseModel

from sr_assistant.core.models import ScopusResult
from sr_assistant.core.repositories.base import BaseRepository


class ScopusRepository(BaseRepository):
    """Repository for Scopus search results."""

    def __init__(self, api_key: str):
        self.client = ElsClient(api_key)
        super().__init__()

    def search(self, query: str, review_id: UUID) -> list[ScopusResult]:
        """Search Scopus and store results."""
        try:
            # Execute search
            search = ElsSearch(query, 'scopus')
            search.execute(self.client)
            
            results = []
            for i, doc in enumerate(search.results):
                result = ScopusResult(
                    id=UUID(int=i),  # Generate UUID from index
                    review_id=review_id,
                    scopus_id=doc.get('dc:identifier', ''),
                    title=doc.get('dc:title', ''),
                    abstract=doc.get('dc:description', ''),
                    authors=doc.get('dc:creator', ''),
                    year=int(doc.get('prism:coverDate', '')[:4]),
                    journal=doc.get('prism:publicationName', ''),
                    doi=doc.get('prism:doi', ''),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Scopus search error: {e}")
            raise 