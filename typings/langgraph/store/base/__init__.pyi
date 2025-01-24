"""
This type stub file was generated by pyright.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Iterable, Literal, NamedTuple, Optional, TypedDict, Union, cast
from langchain_core.embeddings import Embeddings
from langgraph.store.base.embed import (
    AEmbeddingsFunc,
    EmbeddingsFunc,
    ensure_embeddings,
    get_text_at_path,
    tokenize_path,
)

"""Base classes and types for persistent key-value stores.

Stores provide long-term memory that persists across threads and conversations.
Supports hierarchical namespaces, key-value storage, and optional vector search.

Core types:
    - BaseStore: Store interface with sync/async operations
    - Item: Stored key-value pairs with metadata
    - Op: Get/Put/Search/List operations
"""

class Item:
    """Represents a stored item with metadata.

    Args:
        value (dict[str, Any]): The stored data as a dictionary. Keys are filterable.
        key (str): Unique identifier within the namespace.
        namespace (tuple[str, ...]): Hierarchical path defining the collection in which this document resides.
            Represented as a tuple of strings, allowing for nested categorization.
            For example: ("documents", 'user123')
        created_at (datetime): Timestamp of item creation.
        updated_at (datetime): Timestamp of last update.
    """

    __slots__ = ...
    def __init__(
        self,
        *,
        value: dict[str, Any],
        key: str,
        namespace: tuple[str, ...],
        created_at: datetime,
        updated_at: datetime,
    ) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def dict(self) -> dict: ...
    def __repr__(self) -> str: ...

class SearchItem(Item):
    """Represents an item returned from a search operation with additional metadata."""

    __slots__ = ...
    def __init__(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
        created_at: datetime,
        updated_at: datetime,
        score: Optional[float] = ...,
    ) -> None:
        """Initialize a result item.

        Args:
            namespace: Hierarchical path to the item.
            key: Unique identifier within the namespace.
            value: The stored value.
            created_at: When the item was first created.
            updated_at: When the item was last updated.
            score: Relevance/similarity score if from a ranked operation.
        """
        ...

    def dict(self) -> dict: ...

class GetOp(NamedTuple):
    """Operation to retrieve a specific item by its namespace and key.

    This operation allows precise retrieval of stored items using their full path
    (namespace) and unique identifier (key) combination.

    ???+ example "Examples"

        Basic item retrieval:
        ```python
        GetOp(namespace=("users", "profiles"), key="user123")
        GetOp(namespace=("cache", "embeddings"), key="doc456")
        ```
    """

    namespace: tuple[str, ...]
    key: str
    ...

class SearchOp(NamedTuple):
    """Operation to search for items within a specified namespace hierarchy.

    This operation supports both structured filtering and natural language search
    within a given namespace prefix. It provides pagination through limit and offset
    parameters.

    Note:
        Natural language search support depends on your store implementation.

    ???+ example "Examples"
        Search with filters and pagination:
        ```python
        SearchOp(
            namespace_prefix=("documents",),
            filter={"type": "report", "status": "active"},
            limit=5,
            offset=10,
        )
        ```

        Natural language search:
        ```python
        SearchOp(
            namespace_prefix=("users", "content"),
            query="technical documentation about APIs",
            limit=20,
        )
        ```
    """

    namespace_prefix: tuple[str, ...]
    filter: Optional[dict[str, Any]] = ...
    limit: int = ...
    offset: int = ...
    query: Optional[str] = ...

NamespacePath = tuple[Union[str, Literal["*"]], ...]
NamespaceMatchType = Literal["prefix", "suffix"]

class MatchCondition(NamedTuple):
    """Represents a pattern for matching namespaces in the store.

    This class combines a match type (prefix or suffix) with a namespace path
    pattern that can include wildcards to flexibly match different namespace
    hierarchies.

    ???+ example "Examples"
        Prefix matching:
        ```python
        MatchCondition(match_type="prefix", path=("users", "profiles"))
        ```

        Suffix matching with wildcard:
        ```python
        MatchCondition(match_type="suffix", path=("cache", "*"))
        ```

        Simple suffix matching:
        ```python
        MatchCondition(match_type="suffix", path=("v1",))
        ```
    """

    match_type: NamespaceMatchType
    path: NamespacePath
    ...

class ListNamespacesOp(NamedTuple):
    """Operation to list and filter namespaces in the store.

    This operation allows exploring the organization of data, finding specific
    collections, and navigating the namespace hierarchy.

    ???+ example "Examples"

        List all namespaces under the "documents" path:
        ```python
        ListNamespacesOp(
            match_conditions=(
                MatchCondition(match_type="prefix", path=("documents",)),
            ),
            max_depth=2,
        )
        ```

        List all namespaces that end with "v1":
        ```python
        ListNamespacesOp(
            match_conditions=(MatchCondition(match_type="suffix", path=("v1",)),),
            limit=50,
        )
        ```

    """

    match_conditions: Optional[tuple[MatchCondition, ...]] = ...
    max_depth: Optional[int] = ...
    limit: int = ...
    offset: int = ...

class PutOp(NamedTuple):
    """Operation to store, update, or delete an item in the store.

    This class represents a single operation to modify the store's contents,
    whether adding new items, updating existing ones, or removing them.
    """

    namespace: tuple[str, ...]
    key: str
    value: Optional[dict[str, Any]]
    index: Optional[Union[Literal[False], list[str]]] = ...

Op = Union[GetOp, SearchOp, PutOp, ListNamespacesOp]
Result = Union[Item, list[Item], list[SearchItem], list[tuple[str, ...]], None]

class InvalidNamespaceError(ValueError):
    """Provided namespace is invalid."""

    ...

class IndexConfig(TypedDict, total=False):
    """Configuration for indexing documents for semantic search in the store.

    If not provided to the store, the store will not support vector search.
    In that case, all `index` arguments to put() and `aput()` operations will be ignored.
    """

    dims: int
    embed: Union[Embeddings, EmbeddingsFunc, AEmbeddingsFunc]
    fields: Optional[list[str]]
    ...

class BaseStore(ABC):
    """Abstract base class for persistent key-value stores.

    Stores enable persistence and memory that can be shared across threads,
    scoped to user IDs, assistant IDs, or other arbitrary namespaces.
    Some implementations may support semantic search capabilities through
    an optional `index` configuration.

    Note:
        Semantic search capabilities vary by implementation and are typically
        disabled by default. Stores that support this feature can be configured
        by providing an `index` configuration at creation time. Without this
        configuration, semantic search is disabled and any `index` arguments
        to storage operations will have no effect.
    """

    __slots__ = ...
    @abstractmethod
    def batch(self, ops: Iterable[Op]) -> list[Result]:
        """Execute multiple operations synchronously in a single batch.

        Args:
            ops: An iterable of operations to execute.

        Returns:
            A list of results, where each result corresponds to an operation in the input.
            The order of results matches the order of input operations.
        """
        ...

    @abstractmethod
    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        """Execute multiple operations asynchronously in a single batch.

        Args:
            ops: An iterable of operations to execute.

        Returns:
            A list of results, where each result corresponds to an operation in the input.
            The order of results matches the order of input operations.
        """
        ...

    def get(self, namespace: tuple[str, ...], key: str) -> Optional[Item]:
        """Retrieve a single item.

        Args:
            namespace: Hierarchical path for the item.
            key: Unique identifier within the namespace.

        Returns:
            The retrieved item or None if not found.
        """
        ...

    def search(
        self,
        namespace_prefix: tuple[str, ...],
        /,
        *,
        query: Optional[str] = ...,
        filter: Optional[dict[str, Any]] = ...,
        limit: int = ...,
        offset: int = ...,
    ) -> list[SearchItem]:
        """Search for items within a namespace prefix.

        Args:
            namespace_prefix: Hierarchical path prefix to search within.
            query: Optional query for natural language search.
            filter: Key-value pairs to filter results.
            limit: Maximum number of items to return.
            offset: Number of items to skip before returning results.

        Returns:
            List of items matching the search criteria.

        ???+ example "Examples"
            Basic filtering:
            ```python
            # Search for documents with specific metadata
            results = store.search(
                ("docs",), filter={"type": "article", "status": "published"}
            )
            ```

            Natural language search (requires vector store implementation):
            ```python
            # Initialize store with embedding configuration
            store = YourStore(  # e.g., InMemoryStore, AsyncPostgresStore
                index={
                    "dims": 1536,  # embedding dimensions
                    "embed": your_embedding_function,  # function to create embeddings
                    "fields": ["text"],  # fields to embed. Defaults to ["$"]
                }
            )

            # Search for semantically similar documents
            results = store.search(
                ("docs",),
                query="machine learning applications in healthcare",
                filter={"type": "research_paper"},
                limit=5,
            )
            ```

            Note: Natural language search support depends on your store implementation
            and requires proper embedding configuration.
        """
        ...

    def put(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
        index: Optional[Union[Literal[False], list[str]]] = ...,
    ) -> None:
        """Store or update an item in the store.

        Args:
            namespace: Hierarchical path for the item, represented as a tuple of strings.
                Example: ("documents", "user123")
            key: Unique identifier within the namespace. Together with namespace forms
                the complete path to the item.
            value: Dictionary containing the item's data. Must contain string keys
                and JSON-serializable values.
            index: Controls how the item's fields are indexed for search:

                - None (default): Use `fields` you configured when creating the store (if any)
                    If you do not initialize the store with indexing capabilities,
                    the `index` parameter will be ignored
                - False: Disable indexing for this item
                - list[str]: List of field paths to index, supporting:
                    - Nested fields: "metadata.title"
                    - Array access: "chapters[*].content" (each indexed separately)
                    - Specific indices: "authors[0].name"

        Note:
            Indexing support depends on your store implementation.
            If you do not initialize the store with indexing capabilities,
            the `index` parameter will be ignored.

        ???+ example "Examples"
            Store item. Indexing depends on how you configure the store.
            ```python
            store.put(("docs",), "report", {"memory": "Will likes ai"})
            ```

            Do not index item for semantic search. Still accessible through get()
            and search() operations but won't have a vector representation.
            ```python
            store.put(("docs",), "report", {"memory": "Will likes ai"}, index=False)
            ```

            Index specific fields for search.
            ```python
            store.put(
                ("docs",), "report", {"memory": "Will likes ai"}, index=["memory"]
            )
            ```
        """
        ...

    def delete(self, namespace: tuple[str, ...], key: str) -> None:
        """Delete an item.

        Args:
            namespace: Hierarchical path for the item.
            key: Unique identifier within the namespace.
        """
        ...

    def list_namespaces(
        self,
        *,
        prefix: Optional[NamespacePath] = ...,
        suffix: Optional[NamespacePath] = ...,
        max_depth: Optional[int] = ...,
        limit: int = ...,
        offset: int = ...,
    ) -> list[tuple[str, ...]]:
        """List and filter namespaces in the store.

        Used to explore the organization of data,
        find specific collections, or navigate the namespace hierarchy.

        Args:
            prefix (Optional[Tuple[str, ...]]): Filter namespaces that start with this path.
            suffix (Optional[Tuple[str, ...]]): Filter namespaces that end with this path.
            max_depth (Optional[int]): Return namespaces up to this depth in the hierarchy.
                Namespaces deeper than this level will be truncated.
            limit (int): Maximum number of namespaces to return (default 100).
            offset (int): Number of namespaces to skip for pagination (default 0).

        Returns:
            List[Tuple[str, ...]]: A list of namespace tuples that match the criteria.
            Each tuple represents a full namespace path up to `max_depth`.

        ???+ example "Examples":
            Setting max_depth=3. Given the namespaces:
            ```python
            # Example if you have the following namespaces:
            # ("a", "b", "c")
            # ("a", "b", "d", "e")
            # ("a", "b", "d", "i")
            # ("a", "b", "f")
            # ("a", "c", "f")
            store.list_namespaces(prefix=("a", "b"), max_depth=3)
            # [("a", "b", "c"), ("a", "b", "d"), ("a", "b", "f")]
            ```
        """
        ...

    async def aget(self, namespace: tuple[str, ...], key: str) -> Optional[Item]:
        """Asynchronously retrieve a single item.

        Args:
            namespace: Hierarchical path for the item.
            key: Unique identifier within the namespace.

        Returns:
            The retrieved item or None if not found.
        """
        ...

    async def asearch(
        self,
        namespace_prefix: tuple[str, ...],
        /,
        *,
        query: Optional[str] = ...,
        filter: Optional[dict[str, Any]] = ...,
        limit: int = ...,
        offset: int = ...,
    ) -> list[SearchItem]:
        """Asynchronously search for items within a namespace prefix.

        Args:
            namespace_prefix: Hierarchical path prefix to search within.
            query: Optional query for natural language search.
            filter: Key-value pairs to filter results.
            limit: Maximum number of items to return.
            offset: Number of items to skip before returning results.

        Returns:
            List of items matching the search criteria.

        ???+ example "Examples"
            Basic filtering:
            ```python
            # Search for documents with specific metadata
            results = await store.asearch(
                ("docs",), filter={"type": "article", "status": "published"}
            )
            ```

            Natural language search (requires vector store implementation):
            ```python
            # Initialize store with embedding configuration
            store = YourStore(  # e.g., InMemoryStore, AsyncPostgresStore
                index={
                    "dims": 1536,  # embedding dimensions
                    "embed": your_embedding_function,  # function to create embeddings
                    "fields": ["text"],  # fields to embed
                }
            )

            # Search for semantically similar documents
            results = await store.asearch(
                ("docs",),
                query="machine learning applications in healthcare",
                filter={"type": "research_paper"},
                limit=5,
            )
            ```

            Note: Natural language search support depends on your store implementation
            and requires proper embedding configuration.
        """
        ...

    async def aput(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
        index: Optional[Union[Literal[False], list[str]]] = ...,
    ) -> None:
        """Asynchronously store or update an item in the store.

        Args:
            namespace: Hierarchical path for the item, represented as a tuple of strings.
                Example: ("documents", "user123")
            key: Unique identifier within the namespace. Together with namespace forms
                the complete path to the item.
            value: Dictionary containing the item's data. Must contain string keys
                and JSON-serializable values.
            index: Controls how the item's fields are indexed for search:

                - None (default): Use `fields` you configured when creating the store (if any)
                    If you do not initialize the store with indexing capabilities,
                    the `index` parameter will be ignored
                - False: Disable indexing for this item
                - list[str]: List of field paths to index, supporting:
                    - Nested fields: "metadata.title"
                    - Array access: "chapters[*].content" (each indexed separately)
                    - Specific indices: "authors[0].name"

        Note:
            Indexing support depends on your store implementation.
            If you do not initialize the store with indexing capabilities,
            the `index` parameter will be ignored.

        ???+ example "Examples"
            Store item. Indexing depends on how you configure the store.
            ```python
            await store.aput(("docs",), "report", {"memory": "Will likes ai"})
            ```

            Do not index item for semantic search. Still accessible through get()
            and search() operations but won't have a vector representation.
            ```python
            await store.aput(
                ("docs",), "report", {"memory": "Will likes ai"}, index=False
            )
            ```

            Index specific fields for search (if store configured to index items):
            ```python
            await store.aput(
                ("docs",),
                "report",
                {
                    "memory": "Will likes ai",
                    "context": [{"content": "..."}, {"content": "..."}],
                },
                index=["memory", "context[*].content"],
            )
            ```
        """
        ...

    async def adelete(self, namespace: tuple[str, ...], key: str) -> None:
        """Asynchronously delete an item.

        Args:
            namespace: Hierarchical path for the item.
            key: Unique identifier within the namespace.
        """
        ...

    async def alist_namespaces(
        self,
        *,
        prefix: Optional[NamespacePath] = ...,
        suffix: Optional[NamespacePath] = ...,
        max_depth: Optional[int] = ...,
        limit: int = ...,
        offset: int = ...,
    ) -> list[tuple[str, ...]]:
        """List and filter namespaces in the store asynchronously.

        Used to explore the organization of data,
        find specific collections, or navigate the namespace hierarchy.

        Args:
            prefix (Optional[Tuple[str, ...]]): Filter namespaces that start with this path.
            suffix (Optional[Tuple[str, ...]]): Filter namespaces that end with this path.
            max_depth (Optional[int]): Return namespaces up to this depth in the hierarchy.
                Namespaces deeper than this level will be truncated to this depth.
            limit (int): Maximum number of namespaces to return (default 100).
            offset (int): Number of namespaces to skip for pagination (default 0).

        Returns:
            List[Tuple[str, ...]]: A list of namespace tuples that match the criteria.
            Each tuple represents a full namespace path up to `max_depth`.

        ???+ example "Examples"
            Setting max_depth=3 with existing namespaces:
            ```python
            # Given the following namespaces:
            # ("a", "b", "c")
            # ("a", "b", "d", "e")
            # ("a", "b", "d", "i")
            # ("a", "b", "f")
            # ("a", "c", "f")

            await store.alist_namespaces(prefix=("a", "b"), max_depth=3)
            # Returns: [("a", "b", "c"), ("a", "b", "d"), ("a", "b", "f")]
            ```
        """
        ...

__all__ = [
    "BaseStore",
    "Item",
    "Op",
    "PutOp",
    "GetOp",
    "SearchOp",
    "ListNamespacesOp",
    "MatchCondition",
    "NamespacePath",
    "NamespaceMatchType",
    "Embeddings",
    "ensure_embeddings",
    "tokenize_path",
    "get_text_at_path",
]
