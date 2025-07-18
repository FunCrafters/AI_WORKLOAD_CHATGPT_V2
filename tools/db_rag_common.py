import logging
import random
from typing import Any, Dict, List, Optional

import numpy as np
from cachetools import LRUCache, cached
from openai.types.chat import ChatCompletionMessageParam

from db_postgres import execute_query
from workload_embedding import get_embedding_function

# Constants
DEFAULT_RAG_SIMILARITY_THRESHOLD = 0.4
DEFAULT_RAG_SIMILARITY_LIMIT = 4

# Logger
logger = logging.getLogger("DB RAG Common")

query_embedding_cache = LRUCache(maxsize=1024)


@cached(cache=query_embedding_cache)
def generate_query_embedding(query: str) -> Optional[List[float]]:
    try:
        embedding_function = get_embedding_function()
        if not embedding_function:
            logger.error("Failed to get embedding function")
            return None

        embedding = embedding_function.embed_query(query)
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None


def generate_embedding_from_conv(
    conversation: List["ChatCompletionMessageParam"],
) -> Optional[List[float]]:
    embedding_function = get_embedding_function()
    if not embedding_function:
        logger.error("Failed to get embedding function")
        return None

    messages = []
    for message in conversation:
        if message["role"] in ["user", "assistant"]:
            messages.append(message)

    if not messages:
        return None

    combined_text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)

    return embedding_function.embed_query(combined_text)


rag_search_cache = LRUCache(maxsize=512)


# TODO query_embedding should have EPS for cache.
@cached(
    cache=rag_search_cache,
    key=lambda query_embedding, chunk_section, search_qa, threshold, limit: (
        tuple(query_embedding),
        chunk_section,
        search_qa,
        threshold,
        limit,
    ),
)
def execute_rag_search(
    query_embedding: List[float],
    chunk_section: str | None = None,
    search_qa: bool = False,
    threshold: float = DEFAULT_RAG_SIMILARITY_THRESHOLD,
    limit: int = DEFAULT_RAG_SIMILARITY_LIMIT,
) -> List[Dict[str, Any]]:
    """
    Execute RAG similarity search in PostgreSQL

    Args:
        query_embedding: Vector embedding for the query
        chunk_section: The chunk_section to filter by (e.g., 'LOCATIONS', 'CHAMPIONS'). If None, search all sections.
        search_qa: If True, search for QA content in rag_qa_vectors; if False, search for non-QA content in rag_vectors
        threshold: Minimum similarity threshold
        limit: Maximum number of results

    Returns:
        List of dictionaries with chunk_text, metadata, and similarity
    """
    try:
        if search_qa:
            if chunk_section:
                # Search for QA results in separate rag_qa_vectors table
                # Use entity_names from the corresponding chunk_section in main table
                query = """
                    SELECT qa.chunk_text, qa.metadata, 1 - (qa.embedding <=> %s::vector) as similarity
                    FROM rag_qa_vectors qa
                    WHERE qa.metadata->>'entity_name' IN (
                        SELECT DISTINCT metadata->>'entity_name' 
                        FROM rag_vectors 
                        WHERE metadata->>'chunk_section' = %s
                    )
                    AND 1 - (qa.embedding <=> %s::vector) >= %s
                    ORDER BY similarity DESC
                    LIMIT %s
                """
                params = (
                    query_embedding,
                    chunk_section,
                    query_embedding,
                    threshold,
                    limit,
                )
            else:
                # Search all QA results without chunk_section filter
                query = """
                    SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
                    FROM rag_qa_vectors
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY similarity DESC
                    LIMIT %s
                """
                params = (query_embedding, query_embedding, threshold, limit)
        else:
            if chunk_section:
                # Search for similarity results (non-QA) in main rag_vectors table with chunk_section filter
                query = """
                    SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
                    FROM rag_vectors 
                    WHERE metadata->>'chunk_section' = %s
                    AND NOT (metadata->>'chunk_name' LIKE '%%QA%%')
                    AND 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY similarity DESC
                    LIMIT %s
                """
                params = (
                    query_embedding,
                    chunk_section,
                    query_embedding,
                    threshold,
                    limit,
                )
            else:
                # Search all similarity results without chunk_section filter
                query = """
                    SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
                    FROM rag_vectors 
                    WHERE NOT (metadata->>'chunk_name' LIKE '%%QA%%')
                    AND 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY similarity DESC
                    LIMIT %s
                """
                params = (query_embedding, query_embedding, threshold, limit)

        return execute_query(query, params)

    except Exception as e:
        logger.error(f"Error in RAG search: {str(e)}")
        return []


def process_rag_results(
    results: List[Dict[str, Any]], is_qa: bool = False, random_selection: bool = False
) -> str:
    """
    Process RAG search results into formatted content

    Args:
        results: List of dictionaries from execute_rag_search
        is_qa: If True, format as Q&A results
        random_selection: If True, randomly select single result; if False, return all results as text

    Returns:
        Formatted string content or empty string if no results
    """
    if not results:
        return ""

    # Convert results to standard format
    processed_results = []
    for row in results:
        chunk_text = row["chunk_text"]
        metadata = row["metadata"]
        similarity_score = row["similarity"]
        processed_results.append(
            {
                "content": chunk_text,
                "metadata": metadata,
                "similarity": float(similarity_score),
            }
        )

    if not processed_results:
        return ""

    # Handle random selection (for smalltalk) vs all results (for RAG)
    if random_selection:
        # Single random result (for smalltalk)
        selected_result = random.choice(processed_results)
        name = (
            selected_result["metadata"].get("entity_name", "unknown")
            if selected_result["metadata"]
            else "unknown"
        )

        if is_qa:
            return f"### Q&A: {name}\n{selected_result['content']}"
        else:
            return f"### {name}\n{selected_result['content']}"
    else:
        # All results as text (for RAG)
        content_parts = []
        for result in processed_results:
            content_parts.append(result["content"])

        return "\n\n".join(content_parts)


def create_rag_response(
    query: str,
    category: str,
    function_name: str,
    similarity_content: str = "",
    qa_content: str = "",
    error_message: str = "",
    error_details: str = "",
) -> dict:
    """
    Create standardized JSON response for RAG functions

    Args:
        query: Original search query
        category: Category name (e.g., 'locations', 'mechanics')
        function_name: Name of the calling function
        similarity_content: Formatted similarity results content
        qa_content: Formatted QA results content
        error_message: Error message if any
        error_details: Additional error details

    Returns:
        JSON formatted response string
    """
    has_similarity = similarity_content and similarity_content.strip()
    has_qa = qa_content and qa_content.strip()

    # Determine status and message
    if error_message:
        status = "error"
        message = error_message
    elif has_similarity or has_qa:
        status = "success"
        message = f"Found {category} information for '{query}'"
    else:
        status = "error"
        message = f"No {category} information found for query '{query}'"

    # Build response
    response = {
        "status": status,
        "message": message,
        "search_query": query,
        "category": category,
        "content": {
            "similarity_results": similarity_content if has_similarity else "",
            "qa_results": qa_content if has_qa else "",
        },
        "internal_info": {
            "function_name": function_name,
            "parameters": {"query": query},
        },
    }

    # Add error details if present
    if error_details:
        response["internal_info"]["error"] = error_details

    return response


def execute_universal_rag(
    query: str,
    chunk_section: str | None = None,
    category: str = "general",
    function_name: str = "execute_universal_rag",
    threshold: float = DEFAULT_RAG_SIMILARITY_THRESHOLD,
    limit: int = DEFAULT_RAG_SIMILARITY_LIMIT,
    include_qa: bool = True,
) -> dict:
    """
    Universal RAG function that handles the complete RAG workflow

    Args:
        query: Search query string
        chunk_section: Database chunk_section to filter by
        category: Category name for response formatting
        function_name: Name of calling function for internal info
        threshold: Similarity threshold
        limit: Result limit
        include_qa: Whether to search for QA results separately

    Returns:
        JSON formatted response string
    """
    try:
        # Generate embedding
        query_embedding = generate_query_embedding(query)
        if not query_embedding:
            return create_rag_response(
                query=query,
                category=category,
                function_name=function_name,
                error_message=f"Failed to generate embedding for query '{query}'",
            )

        # Search for similarity results
        similarity_results = execute_rag_search(
            query_embedding=query_embedding,
            chunk_section=chunk_section,
            search_qa=False,
            threshold=threshold,
            limit=limit,
        )

        similarity_content = process_rag_results(
            similarity_results, is_qa=False, random_selection=False
        )

        # Search for QA results if requested
        qa_content = ""
        if include_qa:
            qa_results = execute_rag_search(
                query_embedding=query_embedding,
                chunk_section=chunk_section,
                search_qa=True,
                threshold=threshold,
                limit=limit,
            )
            qa_content = process_rag_results(
                qa_results, is_qa=True, random_selection=False
            )

        # Create and return response
        return create_rag_response(
            query=query,
            category=category,
            function_name=function_name,
            similarity_content=similarity_content,
            qa_content=qa_content,
        )

    except Exception as e:
        logger.error(f"Error in universal RAG function: {str(e)}")
        return create_rag_response(
            query=query,
            category=category,
            function_name=function_name,
            error_message=f"Database error while searching for {category} '{query}'",
            error_details=str(e),
        )


def search_qa_similarity(
    query_embedding: List[float],
    limit: int = DEFAULT_RAG_SIMILARITY_LIMIT,
) -> List[Dict[str, Any]]:
    """
    Search QA vectors table for similar content using embeddings

    Args:
        query_embedding: Vector embedding to compare against
        threshold: Minimum similarity threshold
        limit: Maximum number of results

    Returns:
        List of dictionaries with similarity score and QA content
    """
    try:
        query = """
            SELECT 
                id, 
                1 - (embedding <=> %s::vector) as similarity,
                chunk_text,
                embedding
            FROM rag_qa_vectors
            ORDER BY similarity DESC
            LIMIT %s
        """
        params = (query_embedding, limit)

        results = execute_query(query, params)
        return [
            {
                "id": r["id"],
                "similarity": float(r["similarity"]),
                "content": r["chunk_text"],
                "embedding": np.array(
                    [float(x) for x in r["embedding"].strip("[]").split(",")]
                ),
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"Error searching QA vectors: {str(e)}")
        return []
