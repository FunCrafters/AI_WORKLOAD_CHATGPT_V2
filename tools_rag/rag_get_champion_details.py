#!/usr/bin/env python3
"""
RAG tool: Get champion details
Get detailed information about a specific champion from RAG database
"""

import json
from workload_rag_search import rag_search


def rag_get_champion_details(champion_name: str) -> str:
    """
    Get detailed information about a specific champion (OpenAI Function Calling format)
    
    Args:
        champion_name: Name of the champion to get details for
        
    Returns:
        str: JSON formatted detailed information with separated QA and similarity results
    """
    # Get similarity results only
    similarity_config = {
        "base_filters": {"name": champion_name},
        "required_sections": [
            {"name": champion_name, "section": "CORE INFORMATION"},
            {"name": champion_name, "section": "GAMEPLAY INFORMATION"}
        ],
        "similarity_chunks": 7,
        "qa_chunks": 0
    }
    similarity_results = rag_search(champion_name, similarity_config)
    
    # Get QA results only
    qa_config = {
        "base_filters": {"name": champion_name},
        "required_sections": [],
        "similarity_chunks": 0,
        "qa_chunks": 7
    }
    qa_results = rag_search(champion_name, qa_config)
    
    # Check if we have any results
    has_similarity = similarity_results and similarity_results.strip()
    has_qa = qa_results and qa_results.strip()
    
    if not has_similarity and not has_qa:
        return json.dumps({
            "status": "error",
            "message": f"No information found for champion '{champion_name}'",
            "champion_name": champion_name,
            "content": {
                "similarity_results": "",
                "qa_results": ""
            },
            "internal_info": {
                "function_name": "rag_get_champion_details",
                "parameters": {"champion_name": champion_name}
            }
        })
    
    return json.dumps({
        "status": "success", 
        "message": f"Found detailed information for champion '{champion_name}'",
        "champion_name": champion_name,
        "content": {
            "similarity_results": similarity_results if has_similarity else "",
            "qa_results": qa_results if has_qa else ""
        },
        "internal_info": {
            "function_name": "rag_get_champion_details",
            "parameters": {"champion_name": champion_name}
        }
    })


def rag_get_champion_details_text(champion_name: str) -> str:
    """
    Get detailed information about a specific champion (text format for backward compatibility)
    
    Args:
        champion_name: Name of the champion to get details for
        
    Returns:
        str: Detailed information about the champion in text format
    """
    search_config = {
        "base_filters": {"name": champion_name},
        "required_sections": [
            {"name": champion_name, "section": "CORE INFORMATION"},
            {"name": champion_name, "section": "GAMEPLAY INFORMATION"}
        ],
        "similarity_chunks": 7,
        "qa_chunks": 7
    }
    
    return rag_search(champion_name, search_config)