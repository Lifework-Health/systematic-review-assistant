"""
This type stub file was generated by pyright.
"""

from typing import Any, Awaitable, Callable, Sequence, Union
from langchain_core.embeddings import Embeddings

"""Utilities for working with embedding functions and LangChain's Embeddings interface.

This module provides tools to wrap arbitrary embedding functions (both sync and async)
into LangChain's Embeddings interface. This enables using custom embedding functions
with LangChain-compatible tools while maintaining support for both synchronous and
asynchronous operations.
"""
EmbeddingsFunc = Callable[[Sequence[str]], list[list[float]]]
AEmbeddingsFunc = Callable[[Sequence[str]], Awaitable[list[list[float]]]]

def ensure_embeddings(
    embed: Union[Embeddings, EmbeddingsFunc, AEmbeddingsFunc, None],
) -> Embeddings:
    """Ensure that an embedding function conforms to LangChain's Embeddings interface.

    This function wraps arbitrary embedding functions to make them compatible with
    LangChain's Embeddings interface. It handles both synchronous and asynchronous
    functions.

    Args:
        embed: Either an existing Embeddings instance, or a function that converts
            text to embeddings. If the function is async, it will be used for both
            sync and async operations.

    Returns:
        An Embeddings instance that wraps the provided function(s).

    ??? example "Examples"
        Wrap a synchronous embedding function:
        ```python
        def my_embed_fn(texts):
            return [[0.1, 0.2] for _ in texts]

        embeddings = ensure_embeddings(my_embed_fn)
        result = embeddings.embed_query("hello")  # Returns [0.1, 0.2]
        ```

        Wrap an asynchronous embedding function:
        ```python
        async def my_async_fn(texts):
            return [[0.1, 0.2] for _ in texts]

        embeddings = ensure_embeddings(my_async_fn)
        result = await embeddings.aembed_query("hello")  # Returns [0.1, 0.2]
        ```
    """
    ...

class EmbeddingsLambda(Embeddings):
    """Wrapper to convert embedding functions into LangChain's Embeddings interface.

    This class allows arbitrary embedding functions to be used with LangChain-compatible
    tools. It supports both synchronous and asynchronous operations, and can handle:
    1. A synchronous function for sync operations (async operations will use sync function)
    2. An async function for both sync/async operations (sync operations will raise an error)

    The embedding functions should convert text into fixed-dimensional vectors that
    capture the semantic meaning of the text.

    Args:
        func: Function that converts text to embeddings. Can be sync or async.
            If async, it will be used for async operations, but sync operations
            will raise an error. If sync, it will be used for both sync and async operations.

    ??? example "Examples"
        With a sync function:
        ```python
        def my_embed_fn(texts):
            # Return 2D embeddings for each text
            return [[0.1, 0.2] for _ in texts]

        embeddings = EmbeddingsLambda(my_embed_fn)
        result = embeddings.embed_query("hello")  # Returns [0.1, 0.2]
        await embeddings.aembed_query("hello")  # Also returns [0.1, 0.2]
        ```

        With an async function:
        ```python
        async def my_async_fn(texts):
            return [[0.1, 0.2] for _ in texts]

        embeddings = EmbeddingsLambda(my_async_fn)
        await embeddings.aembed_query("hello")  # Returns [0.1, 0.2]
        # Note: embed_query() would raise an error
        ```
    """
    def __init__(self, func: Union[EmbeddingsFunc, AEmbeddingsFunc]) -> None: ...
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts into vectors.

        Args:
            texts: list of texts to convert to embeddings.

        Returns:
            list of embeddings, one per input text. Each embedding is a list of floats.

        Raises:
            ValueError: If the instance was initialized with only an async function.
        """
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a single piece of text.

        Args:
            text: Text to convert to an embedding.

        Returns:
            Embedding vector as a list of floats.

        Note:
            This is equivalent to calling embed_documents with a single text
            and taking the first result.
        """
        ...

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Asynchronously embed a list of texts into vectors.

        Args:
            texts: list of texts to convert to embeddings.

        Returns:
            list of embeddings, one per input text. Each embedding is a list of floats.

        Note:
            If no async function was provided, this falls back to the sync implementation.
        """
        ...

    async def aembed_query(self, text: str) -> list[float]:
        """Asynchronously embed a single piece of text.

        Args:
            text: Text to convert to an embedding.

        Returns:
            Embedding vector as a list of floats.

        Note:
            This is equivalent to calling aembed_documents with a single text
            and taking the first result.
        """
        ...

def get_text_at_path(obj: Any, path: Union[str, list[str]]) -> list[str]:
    """Extract text from an object using a path expression or pre-tokenized path.

    Args:
        obj: The object to extract text from
        path: Either a path string or pre-tokenized path list.

    !!! info "Path types handled"
        - Simple paths: "field1.field2"
        - Array indexing: "[0]", "[*]", "[-1]"
        - Wildcards: "*"
        - Multi-field selection: "{field1,field2}"
        - Nested paths in multi-field: "{field1,nested.field2}"
    """
    ...

def tokenize_path(path: str) -> list[str]:
    """Tokenize a path into components.

    !!! info "Types handled"
        - Simple paths: "field1.field2"
        - Array indexing: "[0]", "[*]", "[-1]"
        - Wildcards: "*"
        - Multi-field selection: "{field1,field2}"
    """
    ...

__all__ = ["ensure_embeddings", "EmbeddingsFunc", "AEmbeddingsFunc"]
