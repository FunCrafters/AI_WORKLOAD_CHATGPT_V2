#!/usr/bin/env python3
"""
GCS Tool: Get Character Details by ID
Get detailed information about a specific character (champion or enemy) by internal ID from GCS database
"""

import json
import logging
from db_gcs import execute_query
from .gcs_common import format_battle_id, get_character_power_ranking, format_abilities_description, get_character_abilities

# Logger
logger = logging.getLogger("GCS Get Character Details by ID")


def gcs_get_character_details_by_id(character_id: str) -> str:
    """
    Get detailed information about a character (champion or enemy) by their internal ID.
    
    Args:
        character_id: Internal character ID from the database
        
    Returns:
        str: JSON formatted detailed character information
    """
    try:
        # First, validate that the character exists and get basic info
        validation_query = """
        SELECT id, name, entity_type
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
                    "function_name": "gcs_get_character_details_by_id",
                    "parameters": {"character_id": character_id}
                }
            })
        
        character_info = validation_result[0]
        entity_type = character_info['entity_type']
        
        if entity_type == 'champion':
            return _get_champion_details_by_id(character_id)
        elif entity_type == 'enemy':
            return _get_enemy_details_by_id(character_id)
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unknown entity type '{entity_type}' for character ID '{character_id}'",
                "character_id": character_id,
                "internal_info": {
                    "function_name": "gcs_get_character_details_by_id",
                    "parameters": {"character_id": character_id}
                }
            })
            
    except Exception as e:
        logger.error(f"Error in gcs_get_character_details_by_id: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving character details: {str(e)}",
            "character_id": character_id,
            "internal_info": {
                "function_name": "gcs_get_character_details_by_id",
                "parameters": {"character_id": character_id}
            }
        })


def _get_champion_details_by_id(champion_id: str) -> str:
    """Get detailed champion information by ID."""
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
                "message": f"No champion data found for ID '{champion_id}'",
                "champion_id": champion_id,
                "internal_info": {
                    "function_name": "gcs_get_character_details_by_id",
                    "parameters": {"character_id": champion_id}
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
        
        # Get similar champions by stats
        similar_champions = _get_similar_characters(champion_id, champion, 'champion')
        
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
            "similar_champions": similar_champions,
            "summary": f"{champion['name']}: {champion.get('rarity', 'N/A')} {champion.get('affinity', 'N/A')} {champion.get('class_type', 'N/A')}, Power: {total_power}, Rank: {ranking.get('summary', 'N/A')}",
            "llm_cache_duration": 3,
            "internal_info": {
                "function_name": "gcs_get_character_details_by_id",
                "parameters": {"character_id": champion_id}
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting champion details for {champion_id}: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving champion details: {str(e)}",
            "champion_id": champion_id,
            "internal_info": {
                "function_name": "gcs_get_character_details_by_id",
                "parameters": {"character_id": champion_id}
            }
        })


def _get_enemy_details_by_id(enemy_id: str) -> str:
    """Get detailed enemy information by ID."""
    try:
        # Get basic enemy info with stats
        enemy_query = """
        SELECT ge.*, es.*
        FROM game_entities ge
        LEFT JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.id = ?
        """
        enemy_data = execute_query(enemy_query, (enemy_id,))
        
        if not enemy_data:
            return json.dumps({
                "status": "error",
                "message": f"No enemy data found for ID '{enemy_id}'",
                "enemy_id": enemy_id,
                "internal_info": {
                    "function_name": "gcs_get_character_details_by_id",
                    "parameters": {"character_id": enemy_id}
                }
            })
        
        enemy = enemy_data[0]
        
        # Get abilities
        abilities_with_effects = get_character_abilities(enemy_id)
        
        # Get traits
        traits_query = """
        SELECT trait_category, trait_value
        FROM entity_traits
        WHERE entity_id = ?
        ORDER BY trait_category
        """
        traits = execute_query(traits_query, (enemy_id,))
        
        # Handle tutorial enemies specially
        if enemy_id.startswith('tutorial.'):
            battle_appearances = [{
                'battle_id': 'tutorial',
                'formatted': 'Tutorial',
                'difficulty': 0,
                'mission': 0,
                'battle_number': 0,
                'wave_number': 1,
                'formation_position': 'center'
            }]
            tutorial_info = {
                'is_tutorial': True,
                'tutorial_section': enemy_id.replace('tutorial.', '')
            }
        else:
            # Get battle appearances for regular enemies
            battle_query = """
            SELECT DISTINCT b.id, b.difficulty, b.mission, b.battle_number,
                   bw.wave_number, bw.formation_position
            FROM battle_waves bw
            JOIN battles b ON bw.battle_id = b.id
            WHERE bw.enemy_id = ?
            ORDER BY b.difficulty, b.mission, b.battle_number, bw.wave_number
            LIMIT 10
            """
            battles = execute_query(battle_query, (enemy_id,))
            
            # Format battle information
            battle_appearances = []
            for battle in battles:
                battle_appearances.append({
                    'battle_id': battle['id'],
                    'formatted': format_battle_id(
                        difficulty=battle['difficulty'],
                        mission=battle['mission'],
                        battle=battle['battle_number']
                    ),
                    'difficulty': battle['difficulty'],
                    'mission': battle['mission'],
                    'battle_number': battle['battle_number'],
                    'wave_number': battle['wave_number'],
                    'formation_position': battle['formation_position']
                })
            tutorial_info = {'is_tutorial': False}
        
        # Get similar enemies by stats
        similar_enemies = _get_similar_characters(enemy_id, enemy, 'enemy')
        
        # Get power ranking
        ranking = get_character_power_ranking(enemy_id)
        
        # Calculate total stats
        total_power = (enemy.get('attack', 0) or 0) + (enemy.get('defense', 0) or 0) + (enemy.get('health', 0) or 0)
        
        # Format abilities description in human-readable format
        abilities_formatted = format_abilities_description(abilities_with_effects)
        
        return json.dumps({
            "status": "success",
            "message": f"Found detailed information for enemy '{enemy['name']}'",
            "enemy_id": enemy_id,
            "name": enemy['name'],
            "basic_info": {
                "series": enemy.get('series'),
                "character_name": enemy.get('character_name'),
                "power_level": enemy.get('power_level'),
                "star_rating": enemy.get('star_rating'),
                "description": enemy.get('description'),
                "lore_description": enemy.get('lore_description')
            },
            "classification": {
                "rarity": enemy.get('rarity'),
                "affinity": enemy.get('affinity'),
                "class_type": enemy.get('class_type'),
                "faction": enemy.get('faction')
            },
            "stats": {
                "attack": enemy.get('attack', 0),
                "defense": enemy.get('defense', 0),
                "health": enemy.get('health', 0),
                "speed": enemy.get('speed', 0),
                "accuracy": enemy.get('accuracy', 0),
                "resistance": enemy.get('resistance', 0),
                "critical_rate": enemy.get('critical_rate', 0),
                "critical_damage": enemy.get('critical_damage', 0),
                "mana": enemy.get('mana', 0),
                "total_power": total_power
            },
            "abilities": abilities_with_effects,
            "abilities_formatted": abilities_formatted,
            "traits": traits,
            "power_ranking": ranking,
            "battle_appearances": battle_appearances,
            "battle_appearances_count": len(battle_appearances),
            "tutorial_info": tutorial_info,
            "similar_enemies": similar_enemies,
            "summary": f"{enemy['name']}: {enemy.get('rarity', 'N/A')} {enemy.get('affinity', 'N/A')} {enemy.get('class_type', 'N/A')}, Power: {total_power}, Appears in {len(battle_appearances)} battles",
            "internal_info": {
                "function_name": "gcs_get_character_details_by_id",
                "parameters": {"character_id": enemy_id}
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting enemy details for {enemy_id}: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving enemy details: {str(e)}",
            "enemy_id": enemy_id,
            "internal_info": {
                "function_name": "gcs_get_character_details_by_id",
                "parameters": {"character_id": enemy_id}
            }
        })


def _get_similar_characters(character_id: str, character_data: dict, entity_type: str) -> list:
    """Get similar characters based on stats comparison."""
    try:
        # Get character stats
        char_attack = character_data.get('attack', 0) or 0
        char_defense = character_data.get('defense', 0) or 0
        char_health = character_data.get('health', 0) or 0
        
        # Find similar characters with similar stats (tolerance of 100 points)
        tolerance = 100
        similar_query = """
        SELECT ge.id, ge.name, es.attack, es.defense, es.health
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.entity_type = ? 
        AND ge.id != ?
        AND ABS(es.attack - ?) <= ?
        AND ABS(es.defense - ?) <= ?
        AND ABS(es.health - ?) <= ?
        ORDER BY (ABS(es.attack - ?) + ABS(es.defense - ?) + ABS(es.health - ?))
        LIMIT 5
        """
        
        similar_results = execute_query(similar_query, (
            entity_type, character_id,
            char_attack, tolerance,
            char_defense, tolerance,
            char_health, tolerance,
            char_attack, char_defense, char_health
        ))
        
        similar_characters = []
        for similar in similar_results:
            # Calculate similarity percentage
            attack_diff = abs(similar['attack'] - char_attack)
            defense_diff = abs(similar['defense'] - char_defense)
            health_diff = abs(similar['health'] - char_health)
            total_diff = attack_diff + defense_diff + health_diff
            
            # Calculate similarity (100% if identical, lower as differences increase)
            max_possible_diff = tolerance * 3  # Max difference across all three stats
            similarity = max(0, (max_possible_diff - total_diff) / max_possible_diff * 100)
            
            similar_characters.append({
                'name': similar['name'],
                'id': similar['id'],
                'similarity': round(similarity, 1),
                'stats': {
                    'attack': similar['attack'],
                    'defense': similar['defense'],
                    'health': similar['health'],
                    'total_power': similar['attack'] + similar['defense'] + similar['health']
                },
                'stat_diff': total_diff
            })
        
        return similar_characters
        
    except Exception as e:
        logger.error(f"Error finding similar characters: {str(e)}")
        return []