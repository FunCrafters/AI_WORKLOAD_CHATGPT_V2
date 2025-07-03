#!/usr/bin/env python3
"""
RAG tool: Get gameplay details
Search gameplay strategies and tactics from RAG database
"""

import json
from workload_rag_search import rag_search


def rag_get_gameplay_details(query: str) -> str:
    """
    Search gameplay information from knowledge base
    
    Args:
        query: Search query for gameplay information
        
    Returns:
        str: JSON formatted gameplay information from knowledge base
    """
    search_config = {
        "base_filters": {"category": "gameplay"},
        "required_sections": [],
        "similarity_chunks": 7,
        "qa_chunks": 7
    }
    
    result = rag_search(query, search_config)
    
    if result and result.strip():
        return json.dumps({
            "status": "success",
            "message": f"Found gameplay information for query: '{query}'",
            "query": query,
            "content": result,
            "internal_info": {
                "function_name": "rag_get_gameplay_details",
                "parameters": {"query": query}
            }
        })
    else:
        return json.dumps({
            "status": "error",
            "message": f"No gameplay information found for query: '{query}'",
            "query": query,
            "content": "",
            "internal_info": {
                "function_name": "rag_get_gameplay_details",
                "parameters": {"query": query}
            }
        })