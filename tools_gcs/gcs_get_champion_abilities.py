#!/usr/bin/env python3
"""
GCS Tool: Get Champion Abilities
Get abilities information for a specific champion from GCS database
"""

import json
import logging
from db_gcs import execute_query
from .gcs_common import get_character_abilities, format_abilities_description

# Logger
logger = logging.getLogger("GCS Get Champion Abilities")


def gcs_get_champion_abilities(champion_name: str) -> str:
    """
    Get abilities information for a champion by name. If single champion found, returns abilities. If multiple found, shows list.

    Args:
        champion_name: Champion name or partial name to search for

    Returns:
        str: JSON formatted champion abilities or list of champions if multiple matches
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
                    "function_name": "gcs_get_champion_abilities",
                    "parameters": {"champion_name": champion_name}
                }
            })
        
        if len(search_results) == 1:
            # Single champion found - return abilities
            champion = search_results[0]
            champion_id = champion['id']
            
            # Get abilities
            abilities_with_effects = get_character_abilities(champion_id)
            abilities_formatted = format_abilities_description(abilities_with_effects)
            
            return json.dumps({
                "status": "success",
                "message": f"Found abilities for champion '{champion['name']}'",
                "champion_id": champion_id,
                "champion_name": champion['name'],
                "basic_info": {
                    "name": champion['name'],
                    "series": champion.get('series'),
                    "character_name": champion.get('character_name'),
                    "rarity": champion.get('rarity'),
                    "affinity": champion.get('affinity'),
                    "class_type": champion.get('class_type')
                },
                "abilities": abilities_with_effects,
                "abilities_formatted": abilities_formatted,
                "abilities_count": len(abilities_with_effects),
                "summary": f"Found {len(abilities_with_effects)} abilities for {champion['name']}",
                "llm_instruction": "Present the abilities information to the user. Use abilities_formatted for human-readable descriptions.",
                "internal_info": {
                    "function_name": "gcs_get_champion_abilities",
                    "parameters": {"champion_name": champion_name}
                }
            })
        else:
            # Multiple champions found - return list
            return json.dumps({
                "status": "success",
                "message": f"Found {len(search_results)} champions matching '{champion_name}'",
                "champion_name": champion_name,
                "multiple_champions": search_results,
                "total_found": len(search_results),
                "guidance": "Multiple champions found. Use gcs_get_champion_abilities with specific champion name or gcs_get_character_abilities_by_id with specific champion ID for abilities analysis.",
                "llm_instruction": "Show the list of champions to the user and ask them to specify which one they want abilities for.",
                "llm_cache_duration": 0,
                "internal_info": {
                    "function_name": "gcs_get_champion_abilities",
                    "parameters": {"champion_name": champion_name}
                }
            })
            
    except Exception as e:
        logger.error(f"Error in gcs_get_champion_abilities: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching for champion abilities: {str(e)}",
            "champion_name": champion_name,
            "internal_info": {
                "function_name": "gcs_get_champion_abilities",
                "parameters": {"champion_name": champion_name}
            }
        })