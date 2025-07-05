#!/usr/bin/env python3
"""
Common functions for RAG operations
Shared utilities for all db_rag_get_* functions
"""

import json
import logging
import random
from typing import List, Dict, Any, Optional
from workload_embedding import get_vectorstore
from db_postgres import execute_query

# Constants
SIMILARITY_THRESHOLD = 0.4
SIMILARITY_LIMIT = 10

# Logger
logger = logging.getLogger("DB RAG Common")

def generate_query_embedding(query: str) -> Optional[List[float]]:
    """
    Generate embedding for query using Ollama
    
    Args:
        query: Search query string
        
    Returns:
        List of floats representing the embedding, or None if failed
    """
    try:
        vectorstore = get_vectorstore()
        if not vectorstore:
            logger.error("Failed to get vectorstore")
            return None
        
        embedding = vectorstore._embedding_function.embed_query(query)
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None

def execute_rag_search(
    query_embedding: List[float], 
    chunk_section: str, 
    search_qa: bool = False,
    threshold: float = SIMILARITY_THRESHOLD,
    limit: int = SIMILARITY_LIMIT
) -> List[Dict[str, Any]]:
    """
    Execute RAG similarity search in PostgreSQL
    
    Args:
        query_embedding: Vector embedding for the query
        chunk_section: The chunk_section to filter by (e.g., 'LOCATIONS', 'CHAMPIONS')
        search_qa: If True, search for QA content in rag_qa_vectors; if False, search for non-QA content in rag_vectors
        threshold: Minimum similarity threshold
        limit: Maximum number of results
        
    Returns:
        List of dictionaries with chunk_text, metadata, and similarity
    """
    try:
        if search_qa:
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
            params = (query_embedding, chunk_section, query_embedding, threshold, limit)
        else:
            # Search for similarity results (non-QA) in main rag_vectors table
            query = """
                SELECT chunk_text, metadata, 1 - (embedding <=> %s::vector) as similarity
                FROM rag_vectors 
                WHERE metadata->>'chunk_section' = %s
                AND NOT (metadata->>'chunk_name' LIKE '%%QA%%')
                AND 1 - (embedding <=> %s::vector) >= %s
                ORDER BY similarity DESC
                LIMIT %s
            """
            params = (query_embedding, chunk_section, query_embedding, threshold, limit)
        
        return execute_query(query, params)
        
    except Exception as e:
        logger.error(f"Error in RAG search: {str(e)}")
        return []

def process_rag_results(
    results: List[Dict[str, Any]], 
    is_qa: bool = False,
    random_selection: bool = True
) -> str:
    """
    Process RAG search results into formatted content
    
    Args:
        results: List of dictionaries from execute_rag_search
        is_qa: If True, format as Q&A results
        random_selection: If True, randomly select from results; if False, use first result
        
    Returns:
        Formatted string content or empty string if no results
    """
    if not results:
        return ""
    
    # Convert results to standard format
    processed_results = []
    for row in results:
        chunk_text = row['chunk_text']
        metadata = row['metadata']
        similarity_score = row['similarity']
        processed_results.append({
            'content': chunk_text,
            'metadata': metadata,
            'similarity': float(similarity_score)
        })
    
    if not processed_results:
        return ""
    
    # Select result (random or first)
    if random_selection:
        selected_result = random.choice(processed_results)
    else:
        selected_result = processed_results[0]
    
    # Extract entity name
    name = selected_result['metadata'].get('entity_name', 'unknown') if selected_result['metadata'] else 'unknown'
    
    # Format content
    if is_qa:
        return f"### Q&A: {name}\n{selected_result['content']}"
    else:
        return f"### {name}\n{selected_result['content']}"

def create_rag_response(
    query: str,
    category: str,
    function_name: str,
    similarity_content: str = "",
    qa_content: str = "",
    error_message: str = "",
    error_details: str = ""
) -> str:
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
            "qa_results": qa_content if has_qa else ""
        },
        "internal_info": {
            "function_name": function_name,
            "parameters": {"query": query}
        }
    }
    
    # Add error details if present
    if error_details:
        response["internal_info"]["error"] = error_details
    
    return json.dumps(response)

def execute_universal_rag(
    query: str,
    chunk_section: str,
    category: str,
    function_name: str,
    threshold: float = SIMILARITY_THRESHOLD,
    limit: int = SIMILARITY_LIMIT,
    include_qa: bool = True
) -> str:
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
                error_message=f"Failed to generate embedding for query '{query}'"
            )
        
        # Search for similarity results
        similarity_results = execute_rag_search(
            query_embedding=query_embedding,
            chunk_section=chunk_section,
            search_qa=False,
            threshold=threshold,
            limit=limit
        )
        
        similarity_content = process_rag_results(similarity_results, is_qa=False)
        
        # Search for QA results if requested
        qa_content = ""
        if include_qa:
            qa_results = execute_rag_search(
                query_embedding=query_embedding,
                chunk_section=chunk_section,
                search_qa=True,
                threshold=threshold,
                limit=limit
            )
            qa_content = process_rag_results(qa_results, is_qa=True)
        
        # Create and return response
        return create_rag_response(
            query=query,
            category=category,
            function_name=function_name,
            similarity_content=similarity_content,
            qa_content=qa_content
        )
        
    except Exception as e:
        logger.error(f"Error in universal RAG function: {str(e)}")
        return create_rag_response(
            query=query,
            category=category,
            function_name=function_name,
            error_message=f"Database error while searching for {category} '{query}'",
            error_details=str(e)
        )