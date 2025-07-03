#!/usr/bin/env python3
"""
GCS Tool: Get Character Abilities by ID
Get abilities information for a specific character (champion or enemy) by internal ID from GCS database
"""

import json
import logging
from db_gcs import execute_query
from .gcs_common import get_character_abilities, format_abilities_description

# Logger
logger = logging.getLogger("GCS Get Character Abilities by ID")


def gcs_get_character_abilities_by_id(character_id: str) -> str:
    """
    Get abilities information for a character (champion or enemy) by their internal ID.
    
    Args:
        character_id: Internal character ID from the database
        
    Returns:
        str: JSON formatted character abilities information
    """
    try:
        # First, validate that the character exists and get basic info
        validation_query = """
        SELECT id, name, entity_type, series, character_name, rarity, affinity, class_type
        FROM game_entities
        WHERE id = ?
        """
        validation_result = execute_query(validation_query, (character_id,))
        
        if not validation_result:
            return json.dumps({
                "status": "error",
                "message": f"No character found with ID '{character_id}'",
                "character_id": character_id,
                "internal_info": {
                    "function_name": "gcs_get_character_abilities_by_id",
                    "parameters": {"character_id": character_id}
                }
            })
        
        character_info = validation_result[0]
        entity_type = character_info['entity_type']
        
        # Get abilities
        abilities_with_effects = get_character_abilities(character_id)
        abilities_formatted = format_abilities_description(abilities_with_effects)
        
        return json.dumps({
            "status": "success",
            "message": f"Found abilities for {entity_type} '{character_info['name']}'",
            "character_id": character_id,
            "character_name": character_info['name'],
            "entity_type": entity_type,
            "basic_info": {
                "name": character_info['name'],
                "entity_type": entity_type,
                "series": character_info.get('series'),
                "character_name": character_info.get('character_name'),
                "rarity": character_info.get('rarity'),
                "affinity": character_info.get('affinity'),
                "class_type": character_info.get('class_type')
            },
            "abilities": abilities_with_effects,
            "abilities_formatted": abilities_formatted,
            "abilities_count": len(abilities_with_effects),
            "summary": f"Found {len(abilities_with_effects)} abilities for {character_info['name']} ({entity_type})",
            "llm_instruction": "Present the abilities information to the user. Use abilities_formatted for human-readable descriptions.",
            "internal_info": {
                "function_name": "gcs_get_character_abilities_by_id",
                "parameters": {"character_id": character_id}
            }
        })
            
    except Exception as e:
        logger.error(f"Error in gcs_get_character_abilities_by_id: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving character abilities: {str(e)}",
            "character_id": character_id,
            "internal_info": {
                "function_name": "gcs_get_character_abilities_by_id",
                "parameters": {"character_id": character_id}
            }
        })