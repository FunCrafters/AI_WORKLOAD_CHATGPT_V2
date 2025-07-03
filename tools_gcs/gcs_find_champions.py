#!/usr/bin/env python3
"""
GCS Tool: Find Champions
Search for champions only by name from GCS database
"""

import json
import logging
import time
from db_gcs import execute_query

# Logger
logger = logging.getLogger("GCS Find Champions")


def gcs_find_champions(name: str) -> str:
    """
    Search for champions only by name. Returns only champions, no enemies.
    
    Args:
        name: Champion name or partial name to search for
        
    Returns:
        str: JSON formatted search results with champions only
    """
    start_time = time.time()
    
    try:
        # Search for champions only
        search_query = """
        SELECT id, name, entity_type, series, character_name, rarity, affinity, class_type
        FROM game_entities
        WHERE name LIKE ? AND entity_type = 'champion'
        ORDER BY name
        """
        
        search_param = f'%{name}%'
        search_results = execute_query(search_query, (search_param,))
        query_count = 1
        
        execution_time = time.time() - start_time
        
        if not search_results:
            return json.dumps({
                "status": "error",
                "message": f"No champions found matching '{name}'",
                "search_term": name,
                "champions": [],
                "total_found": 0,
                "internal_info": {
                    "function_name": "gcs_find_champions",
                    "parameters": {"name": name}
                }
            })
        
        # Convert results to list of dictionaries
        champions = [dict(result) for result in search_results]
        
        return json.dumps({
            "status": "success",
            "message": f"Found {len(champions)} champions matching '{name}'",
            "search_term": name,
            "total_found": len(champions),
            "champions": champions,
            "summary": f"Champion search results for '{name}': {len(champions)} champions found",
            "internal_info": {
                "function_name": "gcs_find_champions",
                "parameters": {"name": name}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in gcs_find_champions: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching for champions: {str(e)}",
            "search_term": name,
            "champions": [],
            "total_found": 0,
            "internal_info": {
                "function_name": "gcs_find_champions",
                "parameters": {"name": name}
            }
        })