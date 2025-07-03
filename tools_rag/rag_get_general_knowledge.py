#!/usr/bin/env python3
"""
RAG tool: Get general knowledge
Search entire knowledge base without category filters
"""

import json
from workload_rag_search import rag_search


def rag_get_general_knowledge(query: str) -> str:
    """
    Search general knowledge base (OpenAI Function Calling format)
    
    Args:
        query: Search query for knowledge base
        
    Returns:
        str: JSON formatted knowledge information with separated QA and similarity results
    """
    # Get similarity results only
    similarity_config = {
        "base_filters": {},
        "required_sections": [],
        "similarity_chunks": 7,
        "qa_chunks": 0
    }
    similarity_results = rag_search(query, similarity_config)
    
    # Get QA results only
    qa_config = {
        "base_filters": {},
        "required_sections": [],
        "similarity_chunks": 0,
        "qa_chunks": 7
    }
    qa_results = rag_search(query, qa_config)
    
    # Check if we have any results
    has_similarity = similarity_results and similarity_results.strip()
    has_qa = qa_results and qa_results.strip()
    
    if not has_similarity and not has_qa:
        return json.dumps({
            "status": "error",
            "message": f"No information found for query '{query}'",
            "search_query": query,
            "content": {
                "similarity_results": "",
                "qa_results": ""
            },
            "internal_info": {
                "function_name": "rag_get_general_knowledge",
                "parameters": {"query": query}
            }
        })
    
    return json.dumps({
        "status": "success",
        "message": f"Found general knowledge for '{query}'",
        "search_query": query,
        "content": {
            "similarity_results": similarity_results if has_similarity else "",
            "qa_results": qa_results if has_qa else ""
        },
        "internal_info": {
            "function_name": "rag_get_general_knowledge",
            "parameters": {"query": query}
        }
    })


def rag_get_general_knowledge_text(query: str) -> str:
    """
    Search general knowledge base (text format for backward compatibility)
    
    Args:
        query: Search query for knowledge base
        
    Returns:
        str: Knowledge information in text format
    """
    search_config = {
        "base_filters": {},
        "required_sections": [],
        "similarity_chunks": 7,
        "qa_chunks": 7
    }
    
    return rag_search(query, search_config)