#!/usr/bin/env python3
"""
GCS Tool: Find Enemies
Search for enemies only by name from GCS database with battle information
"""

import json
import logging
import time
from db_gcs import execute_query
from .gcs_common import format_battle_id

# Logger
logger = logging.getLogger("GCS Find Enemies")


def gcs_find_enemies(name: str) -> str:
    """
    Search for enemies only by name. Returns only enemies with battle information, no champions.
    
    Args:
        name: Enemy name or partial name to search for
        
    Returns:
        str: JSON formatted search results with enemies and battle appearances
    """
    start_time = time.time()
    
    try:
        # Search for enemies only
        search_query = """
        SELECT id, name, entity_type, series, character_name, rarity, affinity, class_type
        FROM game_entities
        WHERE name LIKE ? AND entity_type = 'enemy'
        ORDER BY name
        """
        
        search_param = f'%{name}%'
        search_results = execute_query(search_query, (search_param,))
        query_count = 1
        
        if not search_results:
            return json.dumps({
                "status": "error",
                "message": f"No enemies found matching '{name}'",
                "search_term": name,
                "enemies": [],
                "total_found": 0,
                "internal_info": {
                    "function_name": "gcs_find_enemies",
                    "parameters": {"name": name}
                }
            })
        
        enemies_with_battles = []
        
        # Process each enemy and add battle information
        for result in search_results:
            enemy_data = dict(result)
            
            # Handle tutorial enemies specially
            if enemy_data['id'].startswith('tutorial.'):
                enemy_data['battle_appearances'] = [{
                    'battle_id': 'tutorial',
                    'formatted': 'Tutorial',
                    'difficulty': 0,
                    'mission': 0,
                    'battle_number': 0
                }]
                enemy_data['battle_count'] = 1
            else:
                # Get battle appearances for regular enemies
                battle_query = """
                SELECT DISTINCT b.id, b.difficulty, b.mission, b.battle_number
                FROM battle_waves bw
                JOIN battles b ON bw.battle_id = b.id
                WHERE bw.enemy_id = ?
                ORDER BY b.difficulty, b.mission, b.battle_number
                LIMIT 5
                """
                battles = execute_query(battle_query, (enemy_data['id'],))
                query_count += 1
                
                # Get total count of battle appearances
                count_query = """
                SELECT COUNT(DISTINCT b.id) as total
                FROM battle_waves bw
                JOIN battles b ON bw.battle_id = b.id
                WHERE bw.enemy_id = ?
                """
                count_result = execute_query(count_query, (enemy_data['id'],))
                query_count += 1
                total_battles = count_result[0]['total'] if count_result else 0
                
                # Format battle information
                enemy_data['battle_appearances'] = []
                for battle in battles:
                    enemy_data['battle_appearances'].append({
                        'battle_id': battle['id'],
                        'formatted': format_battle_id(
                            difficulty=battle['difficulty'],
                            mission=battle['mission'],
                            battle=battle['battle_number']
                        ),
                        'difficulty': battle['difficulty'],
                        'mission': battle['mission'],
                        'battle_number': battle['battle_number']
                    })
                enemy_data['battle_count'] = total_battles
                
            enemies_with_battles.append(enemy_data)
        
        execution_time = time.time() - start_time
        
        return json.dumps({
            "status": "success",
            "message": f"Found {len(enemies_with_battles)} enemies matching '{name}'",
            "search_term": name,
            "total_found": len(enemies_with_battles),
            "enemies": enemies_with_battles,
            "summary": f"Enemy search results for '{name}': {len(enemies_with_battles)} enemies found",
            "internal_info": {
                "function_name": "gcs_find_enemies",
                "parameters": {"name": name}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in gcs_find_enemies: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching for enemies: {str(e)}",
            "search_term": name,
            "enemies": [],
            "total_found": 0,
            "internal_info": {
                "function_name": "gcs_find_enemies",
                "parameters": {"name": name}
            }
        })