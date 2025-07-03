#!/usr/bin/env python3
"""
GCS Tool: Find Champion Details
Get detailed information about a specific champion from GCS database
"""

import json
import logging
from db_gcs import execute_query
from .gcs_common import get_champion_full_details

# Logger
logger = logging.getLogger("GCS Find Champion Details")


def gcs_get_champion_details(champion_name: str) -> str:
    """
    Find champion details by name. If single champion found, returns full details. If multiple found, shows list.

    Args:
        champion_name: Champion name or partial name to search for

    Returns:
        str: JSON formatted champion details or list of champions if multiple matches
    """
    try:
        # Search for champions by name
        search_query = """
        SELECT id, name, entity_type, series, character_name, rarity, affinity, class_type
        FROM game_entities
        WHERE name LIKE ? AND entity_type = 'champion'
        ORDER BY name
        """
        
        search_results = execute_query(search_query, (f'%{champion_name}%',))
        
        if not search_results:
            return json.dumps({
                "status": "error",
                "message": f"No champions found matching '{champion_name}'",
                "champion_name": champion_name,
                "champions": [],
                "internal_info": {
                    "function_name": "gcs_get_champion_details",
                    "parameters": {"champion_name": champion_name}
                }
            })
        
        if len(search_results) == 1:
            # Single champion found - return full details
            champion_id = search_results[0]['id']
            return get_champion_full_details(champion_id, champion_name)
        else:
            # Multiple champions found - return list
            return json.dumps({
                "status": "success",
                "message": f"Found {len(search_results)} champions matching '{champion_name}'",
                "champion_name": champion_name,
                "multiple_champions": search_results,
                "total_found": len(search_results),
                "guidance": "Multiple champions found. Use gcs_get_champion_details with specific champion name for detailed analysis.",
                "llm_cache_duration": 3,
                "internal_info": {
                    "function_name": "gcs_get_champion_details",
                    "parameters": {"champion_name": champion_name}
                }
            })
            
    except Exception as e:
        logger.error(f"Error in gcs_find_champion_details: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching for champion: {str(e)}",
            "champion_name": champion_name,
            "internal_info": {
                "function_name": "gcs_get_champion_details",
                "parameters": {"champion_name": champion_name}
            }
        })
