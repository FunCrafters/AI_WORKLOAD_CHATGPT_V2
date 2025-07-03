#!/usr/bin/env python3
"""
GCS Tool: Find Strongest Enemies
Get the strongest enemies based on total power (attack + defense + health)
"""

import json
import logging
from db_gcs import execute_query

# Logger
logger = logging.getLogger("GCS Find Strongest Enemies")


def gcs_find_strongest_enemies(limit: int = 10) -> str:
    """
    Find the strongest enemies based on total power (attack + defense + health).
    
    Args:
        limit: Number of top enemies to return (default: 10, max: 50)
        
    Returns:
        str: JSON formatted list of strongest enemies with analysis
    """
    try:
        # Validate and cap limit
        limit = min(max(1, limit), 50)
        
        # Query for strongest enemies
        query = """
        SELECT ge.id, ge.name, ge.entity_type, ge.rarity, ge.affinity, ge.class_type, ge.faction,
               es.attack, es.defense, es.health, es.speed,
               (es.attack + es.defense + es.health) as total_power
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.entity_type = 'enemy'
        ORDER BY total_power DESC
        LIMIT ?
        """
        
        enemies = execute_query(query, (limit,))
        
        if not enemies:
            return json.dumps({
                "status": "error",
                "message": "No enemies found in database",
                "enemies": [],
                "count": 0,
                "internal_info": {
                    "function_name": "gcs_find_strongest_enemies",
                    "parameters": {"limit": limit}
                }
            })
        
        # Calculate statistics
        powers = [e['total_power'] for e in enemies]
        highest_power = max(powers)
        lowest_power = min(powers)
        average_power = sum(powers) / len(powers)
        power_range = highest_power - lowest_power
        
        # Distribution analysis
        distribution = {
            'by_affinity': {},
            'by_class': {},
            'by_rarity': {},
            'by_faction': {}
        }
        
        # Add battle appearance counts for enemies
        enemies_with_battles = []
        for enemy in enemies:
            # Count by affinity
            affinity = enemy.get('affinity', 'unknown')
            distribution['by_affinity'][affinity] = distribution['by_affinity'].get(affinity, 0) + 1
            
            # Count by class
            class_type = enemy.get('class_type', 'unknown')
            distribution['by_class'][class_type] = distribution['by_class'].get(class_type, 0) + 1
            
            # Count by rarity
            rarity = enemy.get('rarity', 'unknown')
            distribution['by_rarity'][rarity] = distribution['by_rarity'].get(rarity, 0) + 1
            
            # Count by faction
            faction = enemy.get('faction', 'unknown')
            if faction:
                distribution['by_faction'][faction] = distribution['by_faction'].get(faction, 0) + 1
            
            # Get battle appearance count for each enemy
            if enemy['id'].startswith('tutorial.'):
                enemy['battle_count'] = 1
                enemy['is_tutorial'] = True
            else:
                count_query = """
                SELECT COUNT(DISTINCT b.id) as total
                FROM battle_waves bw
                JOIN battles b ON bw.battle_id = b.id
                WHERE bw.enemy_id = ?
                """
                count_result = execute_query(count_query, (enemy['id'],))
                enemy['battle_count'] = count_result[0]['total'] if count_result else 0
                enemy['is_tutorial'] = False
            
            enemies_with_battles.append(enemy)
        
        # Get top enemy details
        top_enemy = enemies_with_battles[0] if enemies_with_battles else None
        
        # Create summary
        summary_parts = [f"Top {len(enemies_with_battles)} strongest enemies"]
        if top_enemy:
            summary_parts.append(f"{top_enemy['name']} leads with {top_enemy['total_power']} power")
        summary_parts.append(f"Average power: {average_power:.1f}")
        summary = ". ".join(summary_parts)
        
        # Create formatted list for LLM presentation
        enemy_list = []
        for i, enemy in enumerate(enemies_with_battles, 1):
            battle_info = f"appears in {enemy.get('battle_count', 0)} battles"
            if enemy.get('is_tutorial'):
                battle_info = "Tutorial enemy"
            enemy_list.append(f"{i}. **{enemy['name']}** - Power: {enemy['total_power']} ({enemy.get('rarity', 'N/A')} {enemy.get('affinity', 'N/A')} {enemy.get('class_type', 'N/A')}) - {battle_info}")
        
        formatted_list = "\n".join(enemy_list)
        
        return json.dumps({
            "status": "success",
            "message": f"Found {len(enemies_with_battles)} strongest enemies",
            "analysis_type": "strongest_enemies",
            "entity_type": "enemy",
            "enemies": enemies_with_battles,
            "count": len(enemies_with_battles),
            "requested_limit": limit,
            "power_stats": {
                "highest": highest_power,
                "lowest": lowest_power,
                "average": round(average_power, 1),
                "range": power_range
            },
            "distribution": distribution,
            "top_enemy": {
                "name": top_enemy['name'],
                "id": top_enemy['id'],
                "power": top_enemy['total_power'],
                "rarity": top_enemy.get('rarity'),
                "affinity": top_enemy.get('affinity'),
                "class_type": top_enemy.get('class_type'),
                "battle_appearances": top_enemy.get('battle_count', 0)
            } if top_enemy else None,
            "summary": summary,
            "formatted_list": formatted_list,
            "llm_instruction": f"Present the following list of {len(enemies_with_battles)} strongest enemies to the user:\n\n{formatted_list}\n\nThen provide a brief summary of the power statistics and distribution.",
            "internal_info": {
                "function_name": "gcs_find_strongest_enemies",
                "parameters": {"limit": limit}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in gcs_find_strongest_enemies: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error finding strongest enemies: {str(e)}",
            "enemies": [],
            "count": 0,
            "internal_info": {
                "function_name": "gcs_find_strongest_enemies",
                "parameters": {"limit": limit}
            }
        })