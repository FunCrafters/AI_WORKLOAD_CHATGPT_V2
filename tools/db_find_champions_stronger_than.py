#!/usr/bin/env python3
"""
PostgreSQL Database Tool: Find Champions Stronger Than
Find champions who have higher total power than a specified reference champion with optional trait filtering
"""

import json
import logging
from db_postgres import execute_query

# Logger
logger = logging.getLogger("ChampionsStrongerThan")


def db_find_champions_stronger_than(character_name: str, limit: int = 20, rarity: str = None, affinity: str = None, class_type: str = None) -> str:
    """
    Find champions who are stronger than the specified reference champion with optional trait filtering.
    
    Args:
        character_name: Name of the reference champion to compare against
        limit: Maximum number of stronger champions to return (default: 20, max: 50)
        rarity: Filter by rarity (legendary, epic, rare, uncommon, common)
        affinity: Filter by affinity (red, blue, green, yellow, purple)
        class_type: Filter by class type (attacker, defender, support)
        
    Returns:
        str: JSON formatted list of champions stronger than the reference champion
    """
    try:
        # Validate and cap limit
        limit = min(max(1, limit), 50)
        
        # First, find the reference character
        ref_query = """
        SELECT ct.id, ct.champion_name, ct.rarity, ct.affinity, ct.class,
               cs.attack, cs.defense, cs.health, 
               (cs.attack + cs.defense + cs.health) as total_power
        FROM champion_traits ct
        JOIN champion_stats cs ON ct.champion_name = cs.champion_name
        WHERE ct.champion_name ILIKE %s
        LIMIT 1
        """
        
        ref_result = execute_query(ref_query, (f'%{character_name}%',))
        
        if not ref_result:
            return json.dumps({
                "status": "success",
                "message": f"No character found matching '{character_name}'",
                "reference_character": None,
                "stronger_champions": [],
                "count": 0,
                "filters": {
                    "rarity": rarity,
                    "affinity": affinity,
                    "class_type": class_type
                },
                "power_analysis": {"reference_power": 0, "average_difference": 0, "maximum_difference": 0, "minimum_difference": 0},
                "summary": f"No character found matching '{character_name}'",
                "formatted_list": f"No character found matching '{character_name}'. Please check the character name and try again.",
                "llm_instruction": f"No character found matching '{character_name}'. Suggest checking the character name or try a different search term.",
                "internal_info": {
                    "function_name": "db_find_champions_stronger_than",
                    "parameters": {"character_name": character_name, "limit": limit, "rarity": rarity, "affinity": affinity, "class_type": class_type}
                }
            })
        
        ref_char = ref_result[0]
        ref_power = ref_char['total_power']
        
        # Build query conditions for stronger champions
        conditions = [
            "(cs2.attack + cs2.defense + cs2.health) > %s"
        ]
        params = [ref_power]
        
        # Add trait filtering if provided
        if rarity:
            conditions.append("ct2.rarity = %s")
            params.append(rarity.upper())
            
        if affinity:
            conditions.append("ct2.affinity = %s")
            params.append(affinity.upper())
            
        if class_type:
            conditions.append("ct2.class = %s")
            params.append(class_type.upper())
        
        # Add limit parameter
        params.append(limit)
        
        # Find champions stronger than the reference character
        stronger_query = f"""
        SELECT ct2.id, ct2.champion_name, ct2.rarity, ct2.affinity, ct2.class, ct2.faction,
               cs2.attack, cs2.defense, cs2.health, cs2.speed,
               (cs2.attack + cs2.defense + cs2.health) as total_power,
               ((cs2.attack + cs2.defense + cs2.health) - %s) as power_difference
        FROM champion_traits ct2
        JOIN champion_stats cs2 ON ct2.champion_name = cs2.champion_name
        WHERE {' AND '.join(conditions)}
        ORDER BY total_power DESC
        LIMIT %s
        """
        
        # Add ref_power again for power_difference calculation
        query_params = [ref_power] + params
        stronger_chars = execute_query(stronger_query, query_params)
        
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
        
        # Create filter description
        trait_filters = []
        if rarity:
            trait_filters.append(f"rarity={rarity}")
        if affinity:
            trait_filters.append(f"affinity={affinity}")
        if class_type:
            trait_filters.append(f"class_type={class_type}")
        
        filter_text = f" with {', '.join(trait_filters)}" if trait_filters else ""
        
        # Create formatted list for LLM presentation
        if stronger_chars:
            champion_list = []
            for i, champion in enumerate(stronger_chars, 1):
                power_diff = champion['power_difference']
                champion_list.append(
                    f"{i}. **{champion['champion_name']}** - Power: {champion['total_power']} "
                    f"(+{power_diff} stronger) - {champion.get('rarity', 'N/A')} "
                    f"{champion.get('affinity', 'N/A')} {champion.get('class', 'N/A')}"
                )
            formatted_list = "\n".join(champion_list)
            
            llm_instruction = (
                f"Present the following list of {len(stronger_chars)} champions{filter_text} who are stronger than "
                f"**{ref_char['champion_name']}** (power: {ref_power}):\n\n{formatted_list}\n\n"
                f"Then provide a brief summary of the power differences."
            )
        else:
            formatted_list = f"No champions found{filter_text} stronger than {ref_char['champion_name']} (power: {ref_power})"
            llm_instruction = formatted_list
        
        # Create summary
        if stronger_chars:
            summary = (
                f"Found {len(stronger_chars)} champions{filter_text} stronger than {ref_char['champion_name']} "
                f"(power: {ref_power}). Average power difference: {power_analysis['average_difference']}"
            )
        else:
            summary = f"No champions found{filter_text} stronger than {ref_char['champion_name']} (power: {ref_power})"
        
        return json.dumps({
            "status": "success",
            "message": summary,
            "reference_character": {
                "name": ref_char['champion_name'],
                "id": ref_char['id'],
                "power": ref_power,
                "rarity": ref_char.get('rarity'),
                "affinity": ref_char.get('affinity'),
                "class_type": ref_char.get('class'),
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
            "filters": {
                "rarity": rarity,
                "affinity": affinity,
                "class_type": class_type
            },
            "power_analysis": power_analysis,
            "summary": summary,
            "formatted_list": formatted_list,
            "llm_instruction": llm_instruction,
            "internal_info": {
                "function_name": "db_find_champions_stronger_than",
                "parameters": {"character_name": character_name, "limit": limit, "rarity": rarity, "affinity": affinity, "class_type": class_type}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in db_find_champions_stronger_than: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error finding champions stronger than '{character_name}': {str(e)}",
            "reference_character": None,
            "stronger_champions": [],
            "count": 0,
            "filters": {
                "rarity": rarity,
                "affinity": affinity,
                "class_type": class_type
            },
            "internal_info": {
                "function_name": "db_find_champions_stronger_than",
                "parameters": {"character_name": character_name, "limit": limit, "rarity": rarity, "affinity": affinity, "class_type": class_type}
            }
        })