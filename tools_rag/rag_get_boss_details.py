#!/usr/bin/env python3
"""
RAG tool: Get boss details
Get detailed information about a specific boss from RAG database
"""

import json
from workload_rag_search import rag_search


def rag_get_boss_details(boss_name: str) -> str:
    """
    Get detailed information about a specific boss with fallback to champion details (OpenAI Function Calling format)
    
    Args:
        boss_name: Name of the boss to get details for
        
    Returns:
        str: JSON formatted detailed information with separated QA and similarity results
    """
    # First try to find boss-specific information - similarity results
    similarity_config = {
        "base_filters": {"name": boss_name},
        "required_sections": [
            {"name": boss_name, "section": "CORE INFORMATION"},
            {"name": boss_name, "section": "GAMEPLAY INFORMATION"}
        ],
        "similarity_chunks": 7,
        "qa_chunks": 0
    }
    boss_similarity = rag_search(boss_name, similarity_config)
    
    # First try to find boss-specific information - QA results
    qa_config = {
        "base_filters": {"name": boss_name},
        "required_sections": [],
        "similarity_chunks": 0,
        "qa_chunks": 7
    }
    boss_qa = rag_search(boss_name, qa_config)
    
    # Check if we found meaningful boss information
    has_boss_similarity = boss_similarity and len(boss_similarity.strip()) > 50
    has_boss_qa = boss_qa and len(boss_qa.strip()) > 50
    
    if has_boss_similarity or has_boss_qa:
        return json.dumps({
            "status": "success",
            "message": f"Found boss information for '{boss_name}'",
            "boss_name": boss_name,
            "content_type": "boss",
            "content": {
                "similarity_results": boss_similarity if has_boss_similarity else "",
                "qa_results": boss_qa if has_boss_qa else ""
            },
            "internal_info": {
                "function_name": "rag_get_boss_details",
                "parameters": {"boss_name": boss_name}
            }
        })
    
    # Fallback: Try to find champion information for this name
    # Many champions can appear as bosses in different game modes
    from tools_rag.rag_get_champion_details import rag_get_champion_details_text
    champion_result = rag_get_champion_details_text(boss_name)
    
    if champion_result and len(champion_result.strip()) > 50:
        # Add a note that this is champion info being used for boss query
        combined_content = f"=== CHAMPION INFORMATION (used as boss reference) ===\n\n{champion_result}"
        return json.dumps({
            "status": "success",
            "message": f"Found champion information for '{boss_name}' (used as boss reference)",
            "boss_name": boss_name,
            "content_type": "champion_as_boss",
            "content": {
                "similarity_results": combined_content,
                "qa_results": ""
            },
            "internal_info": {
                "function_name": "rag_get_boss_details",
                "parameters": {"boss_name": boss_name}
            }
        })
    
    # If neither boss nor champion info found, return error
    return json.dumps({
        "status": "error",
        "message": f"No information found for boss '{boss_name}'",
        "boss_name": boss_name,
        "content_type": "none",
        "content": {
            "similarity_results": "",
            "qa_results": ""
        },
        "internal_info": {
            "function_name": "rag_get_boss_details",
            "parameters": {"boss_name": boss_name}
        }
    })


def rag_get_boss_details_text(boss_name: str) -> str:
    """
    Get detailed information about a specific boss with fallback to champion details (text format for backward compatibility)
    
    Args:
        boss_name: Name of the boss to get details for
        
    Returns:
        str: Detailed information about the boss, or champion details if boss not found
    """
    # First try to find boss-specific information
    search_config = {
        "base_filters": {"name": boss_name},
        "required_sections": [
            {"name": boss_name, "section": "CORE INFORMATION"},
            {"name": boss_name, "section": "GAMEPLAY INFORMATION"}
        ],
        "similarity_chunks": 7,
        "qa_chunks": 7
    }
    
    boss_result = rag_search(boss_name, search_config)
    
    # Check if we found meaningful boss information
    if boss_result and len(boss_result.strip()) > 50:  # Minimum threshold for meaningful content
        return boss_result
    
    # Fallback: Try to find champion information for this name
    # Many champions can appear as bosses in different game modes
    from tools_rag.rag_get_champion_details import rag_get_champion_details_text
    champion_result = rag_get_champion_details_text(boss_name)
    
    if champion_result and len(champion_result.strip()) > 50:
        # Add a note that this is champion info being used for boss query
        return f"=== CHAMPION INFORMATION (used as boss reference) ===\n\n{champion_result}"
    
    # If neither boss nor champion info found, return empty
    return boss_result if boss_result else ""
