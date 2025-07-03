#!/usr/bin/env python3
"""
GCS Common Functions
Shared utility functions for GCS database tools
"""

import logging
from db_gcs import execute_query

# Logger
logger = logging.getLogger("GCS Common")


def format_battle_id(difficulty: int = None, mission: int = None, battle: int = None) -> str:
    """
    Format battle information in human-readable format.
    
    Args:
        difficulty: Difficulty level (1-5)
        mission: Mission number
        battle: Battle number
        
    Returns:
        str: Formatted battle description
    """
    # Difficulty level mapping
    difficulty_names = {
        1: "Normal",
        2: "Hard", 
        3: "Very Hard",
        4: "Extreme",
        5: "Nightmare"
    }
    
    if difficulty is not None and mission is not None and battle is not None:
        diff_name = difficulty_names.get(difficulty, f"Level {difficulty}")
        return f"Mission: {mission}, Battle: {battle}, Difficulty: {diff_name}"
    
    return "Unknown battle"


def clean_ability_description(description: str) -> str:
    """Clean ability description from game formatting tags and variables"""
    if not description:
        return ""
        
    import re
    
    # Remove style tags like <style=status.cri...>text</style>
    cleaned = re.sub(r'<style=[^>]+>', '', description)
    cleaned = re.sub(r'</style>', '', cleaned)
    
    # Replace variable placeholders with descriptive text
    cleaned = cleaned.replace('{0}', 'X')
    cleaned = cleaned.replace('{1}', 'Y') 
    cleaned = cleaned.replace('{2}', 'Z')
    cleaned = cleaned.replace('{3}', 'N')
    cleaned = cleaned.replace('{4}', 'M')
        
    # Clean up common formatting issues
    cleaned = cleaned.replace('[Battle]', 'Battle')
    cleaned = cleaned.replace('[C. DMG]', 'Critical Damage')
    cleaned = cleaned.replace('[Increase DEF]', 'Defense Increase')
    cleaned = cleaned.replace('[Increase ATK]', 'Attack Increase')
    cleaned = cleaned.replace('[Increase CRIT DMG]', 'Critical Damage Increase')
    
    # Remove extra spaces
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


def get_character_abilities(character_id: str) -> list:
    """
    Get abilities data for a character including effects.
    
    Args:
        character_id: Character ID from database
        
    Returns:
        list: List of abilities with their effects
    """
    try:
        # Get abilities
        abilities_query = """
        SELECT ea.ability_slot, ea.ability_level, a.id as ability_id, a.name,
               a.description, a.short_description, a.max_level
        FROM entity_abilities ea
        JOIN abilities a ON ea.ability_id = a.id
        WHERE ea.entity_id = ?
        ORDER BY
            CASE ea.ability_slot
                WHEN 'basic' THEN 1
                WHEN 'special' THEN 2
                WHEN 'passive' THEN 3
                WHEN 'leader' THEN 4
            END
        """
        abilities = execute_query(abilities_query, (character_id,))
        
        # Get ability effects for each ability
        abilities_with_effects = []
        for ability in abilities:
            effects_query = """
            SELECT level, effect_name, effect_value, effect_description
            FROM ability_effects
            WHERE ability_id = ?
            ORDER BY level
            """
            effects = execute_query(effects_query, (ability['ability_id'],))
            
            abilities_with_effects.append({
                'slot': ability['ability_slot'],
                'name': ability['name'],
                'current_level': ability['ability_level'],
                'max_level': ability['max_level'],
                'description': ability['description'],
                'short_description': ability['short_description'],
                'effects_by_level': effects
            })
        
        return abilities_with_effects
        
    except Exception as e:
        logger.error(f"Error getting abilities for {character_id}: {str(e)}")
        return []


def format_abilities_description(abilities_with_effects: list) -> str:
    """
    Format abilities in a human-readable format similar to the parser version.
    
    Args:
        abilities_with_effects: List of abilities with their effects
        
    Returns:
        str: Formatted abilities description
    """
    if not abilities_with_effects:
        return "No abilities found."
    
    formatted_abilities = []
    
    for ability in abilities_with_effects:
        slot = ability.get('slot', 'unknown').upper()
        name = ability.get('name', 'Unknown')
        description = clean_ability_description(ability.get('description', ''))
        
        # Use description if available, otherwise fall back to short_description
        if not description:
            description = clean_ability_description(ability.get('short_description', ''))
        
        if description:
            formatted_abilities.append(f"• Special Ability: {name} - {description}")
    
    if formatted_abilities:
        return "Abilities:\n  " + "\n  ".join(formatted_abilities)
    else:
        return "No ability descriptions available."


def get_character_power_ranking(character_id: str) -> dict:
    """
    Get character's power ranking among all champions.
    
    Args:
        character_id: Character ID
        
    Returns:
        dict: Character's ranking information
    """
    try:
        # Get character's power
        char_query = """
        SELECT (es.attack + es.defense + es.health) as total_power
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.id = ?
        """
        char_info = execute_query(char_query, (character_id,))
        
        if not char_info:
            return {"error": "Character not found"}
        
        char_power = char_info[0]['total_power']
        
        # Get ranking among champions
        ranking_query = """
        SELECT COUNT(*) + 1 as rank
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.entity_type = 'champion' AND (es.attack + es.defense + es.health) > ?
        """
        ranking_result = execute_query(ranking_query, (char_power,))
        
        # Get total count of champions
        total_query = """
        SELECT COUNT(*) as total
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.entity_type = 'champion'
        """
        total_result = execute_query(total_query)
        
        rank = ranking_result[0]['rank'] if ranking_result else 0
        total = total_result[0]['total'] if total_result else 0
        
        percentile = round((total - rank + 1) / total * 100, 1) if total > 0 else 0
        
        return {
            "rank": rank,
            "total": total,
            "percentile": percentile,
            "power": char_power,
            "summary": f"Rank {rank}/{total} among champions ({percentile}th percentile)"
        }
        
    except Exception as e:
        logger.error(f"Error getting power ranking: {str(e)}")
        return {"error": f"Error calculating ranking: {str(e)}"}


def get_champion_full_details(champion_id: str, original_search: str) -> str:
    """
    Get complete details about a specific champion by ID.
    
    Args:
        champion_id: Champion ID from database
        original_search: Original search term used
        
    Returns:
        str: JSON formatted complete champion information
    """
    import json
    
    try:
        # Get basic champion info with stats
        champion_query = """
        SELECT ge.*, es.*
        FROM game_entities ge
        LEFT JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.id = ?
        """
        champion_data = execute_query(champion_query, (champion_id,))
        
        if not champion_data:
            return json.dumps({
                "status": "error",
                "message": f"No data found for champion {champion_id}",
                "champion_id": champion_id,
                "internal_info": {
                    "function_name": "gcs_get_champion_details",
                    "parameters": {"champion_name": original_search}
                }
            })
        
        champion = champion_data[0]
        
        # Get abilities
        abilities_with_effects = get_character_abilities(champion_id)
        
        # Get traits
        traits_query = """
        SELECT trait_category, trait_value
        FROM entity_traits
        WHERE entity_id = ?
        ORDER BY trait_category
        """
        traits = execute_query(traits_query, (champion_id,))
        
        # Get battles where this champion is recommended
        recommendations_query = """
        SELECT b.id, b.name, b.difficulty, b.mission, b.battle_number, b.energy_cost
        FROM battle_participants bp
        JOIN battles b ON bp.battle_id = b.id
        WHERE bp.participant_id = ? AND bp.participant_type = 'recommended_champion'
        ORDER BY b.difficulty, b.mission, b.battle_number
        """
        recommended_battles = execute_query(recommendations_query, (champion_id,))
        
        # Format recommended battles
        formatted_battles = []
        for battle in recommended_battles:
            formatted_battles.append({
                'battle_id': battle['id'],
                'battle_name': battle['name'],
                'formatted': format_battle_id(
                    difficulty=battle['difficulty'],
                    mission=battle['mission'],
                    battle=battle['battle_number']
                ),
                'energy_cost': battle['energy_cost']
            })
        
        # Get power ranking
        ranking = get_character_power_ranking(champion_id)
        
        # Calculate total stats
        total_power = (champion.get('attack', 0) or 0) + (champion.get('defense', 0) or 0) + (champion.get('health', 0) or 0)
        
        # Format abilities description in human-readable format
        abilities_formatted = format_abilities_description(abilities_with_effects)
        
        return json.dumps({
            "status": "success",
            "message": f"Found detailed information for champion '{champion['name']}'",
            "champion_id": champion_id,
            "name": champion['name'],
            "basic_info": {
                "series": champion.get('series'),
                "character_name": champion.get('character_name'),
                "visual_level": champion.get('visual_level'),
                "visual_stars": champion.get('visual_stars'),
                "description": champion.get('description'),
                "lore_description": champion.get('lore_description')
            },
            "classification": {
                "rarity": champion.get('rarity'),
                "affinity": champion.get('affinity'),
                "class_type": champion.get('class_type'),
                "faction": champion.get('faction')
            },
            "stats": {
                "attack": champion.get('attack', 0),
                "defense": champion.get('defense', 0),
                "health": champion.get('health', 0),
                "speed": champion.get('speed', 0),
                "accuracy": champion.get('accuracy', 0),
                "resistance": champion.get('resistance', 0),
                "critical_rate": champion.get('critical_rate', 0),
                "critical_damage": champion.get('critical_damage', 0),
                "mana": champion.get('mana', 0),
                "total_power": total_power
            },
            "abilities": abilities_with_effects,
            "abilities_formatted": abilities_formatted,
            "traits": traits,
            "power_ranking": ranking,
            "recommended_for_battles": formatted_battles,
            "battle_recommendations_count": len(formatted_battles),
            "summary": f"{champion['name']}: {champion.get('rarity', 'N/A')} {champion.get('affinity', 'N/A')} {champion.get('class_type', 'N/A')}, Power: {total_power}, Rank: {ranking.get('summary', 'N/A')}",
            "llm_cache_duration": 3,
            "internal_info": {
                "function_name": "gcs_get_champion_details",
                "parameters": {"champion_name": original_search}
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting champion details for {champion_id}: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving champion details: {str(e)}",
            "champion_id": champion_id,
            "internal_info": {
                "function_name": "gcs_get_champion_details",
                "parameters": {"champion_name": original_search}
            }
        })