#!/usr/bin/env python3
"""
GCS Tool: Find Champions Stronger Than
Find champions who have higher total power than a specified reference champion
"""

import json
import logging
from db_gcs import execute_query

# Logger
logger = logging.getLogger("GCS Find Champions Stronger Than")


def gcs_find_champions_stronger_than(character_name: str, limit: int = 20) -> str:
    """
    Find champions who are stronger than the specified reference champion.
    
    Args:
        character_name: Name of the reference champion to compare against
        limit: Maximum number of stronger champions to return (default: 20, max: 50)
        
    Returns:
        str: JSON formatted list of champions stronger than the reference champion
    """
    try:
        # Validate and cap limit
        limit = min(max(1, limit), 50)
        
        # First, find the reference character
        ref_query = """
        SELECT ge.id, ge.name, ge.entity_type, ge.rarity, ge.affinity, ge.class_type,
               es.attack, es.defense, es.health, 
               (es.attack + es.defense + es.health) as total_power
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.name LIKE ?
        LIMIT 1
        """
        
        ref_result = execute_query(ref_query, (f'%{character_name}%',))
        
        if not ref_result:
            return json.dumps({
                "status": "error",
                "message": f"No character found matching '{character_name}'",
                "reference_character": None,
                "stronger_champions": [],
                "count": 0,
                "internal_info": {
                    "function_name": "gcs_find_champions_stronger_than",
                    "parameters": {"character_name": character_name, "limit": limit}
                }
            })
        
        ref_char = ref_result[0]
        ref_power = ref_char['total_power']
        
        # Find champions stronger than the reference character
        stronger_query = """
        SELECT ge.id, ge.name, ge.entity_type, ge.rarity, ge.affinity, ge.class_type, ge.faction,
               es.attack, es.defense, es.health, es.speed,
               (es.attack + es.defense + es.health) as total_power,
               ((es.attack + es.defense + es.health) - ?) as power_difference
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE (es.attack + es.defense + es.health) > ? AND ge.entity_type = 'champion'
        ORDER BY total_power DESC
        LIMIT ?
        """
        
        stronger_chars = execute_query(stronger_query, (ref_power, ref_power, limit))
        
        # Calculate power analysis if we have results
        power_analysis = {
            "reference_power": ref_power,
            "average_difference": 0,
            "maximum_difference": 0,
            "minimum_difference": 0
        }
        
        if stronger_chars:
            power_diffs = [char['power_difference'] for char in stronger_chars]
            power_analysis.update({
                "average_difference": round(sum(power_diffs) / len(power_diffs), 1),
                "maximum_difference": max(power_diffs),
                "minimum_difference": min(power_diffs)
            })
        
        # Create formatted list for LLM presentation
        if stronger_chars:
            champion_list = []
            for i, champion in enumerate(stronger_chars, 1):
                power_diff = champion['power_difference']
                champion_list.append(
                    f"{i}. **{champion['name']}** - Power: {champion['total_power']} "
                    f"(+{power_diff} stronger) - {champion.get('rarity', 'N/A')} "
                    f"{champion.get('affinity', 'N/A')} {champion.get('class_type', 'N/A')}"
                )
            formatted_list = "\n".join(champion_list)
            
            llm_instruction = (
                f"Present the following list of {len(stronger_chars)} champions who are stronger than "
                f"**{ref_char['name']}** (power: {ref_power}):\n\n{formatted_list}\n\n"
                f"Then provide a brief summary of the power differences."
            )
        else:
            formatted_list = f"No champions found stronger than {ref_char['name']} (power: {ref_power})"
            llm_instruction = formatted_list
        
        # Create summary
        if stronger_chars:
            summary = (
                f"Found {len(stronger_chars)} champions stronger than {ref_char['name']} "
                f"(power: {ref_power}). Average power difference: {power_analysis['average_difference']}"
            )
        else:
            summary = f"No champions found stronger than {ref_char['name']} (power: {ref_power})"
        
        return json.dumps({
            "status": "success",
            "message": summary,
            "reference_character": {
                "name": ref_char['name'],
                "id": ref_char['id'],
                "power": ref_power,
                "entity_type": ref_char['entity_type'],
                "rarity": ref_char.get('rarity'),
                "affinity": ref_char.get('affinity'),
                "class_type": ref_char.get('class_type'),
                "stats": {
                    "attack": ref_char['attack'],
                    "defense": ref_char['defense'],
                    "health": ref_char['health'],
                    "total_power": ref_power
                }
            },
            "stronger_champions": stronger_chars,
            "count": len(stronger_chars),
            "requested_limit": limit,
            "power_analysis": power_analysis,
            "summary": summary,
            "formatted_list": formatted_list,
            "llm_instruction": llm_instruction,
            "internal_info": {
                "function_name": "gcs_find_champions_stronger_than",
                "parameters": {"character_name": character_name, "limit": limit}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in gcs_find_champions_stronger_than: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error finding champions stronger than '{character_name}': {str(e)}",
            "reference_character": None,
            "stronger_champions": [],
            "count": 0,
            "internal_info": {
                "function_name": "gcs_find_champions_stronger_than",
                "parameters": {"character_name": character_name, "limit": limit}
            }
        })