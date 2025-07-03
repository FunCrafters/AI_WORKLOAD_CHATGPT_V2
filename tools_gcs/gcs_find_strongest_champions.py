#!/usr/bin/env python3
"""
GCS Tool: Find Strongest Champions
Get the strongest champions based on total power (attack + defense + health)
"""

import json
import logging
from db_gcs import execute_query

# Logger
logger = logging.getLogger("GCS Find Strongest Champions")


def gcs_find_strongest_champions(limit: int = 10) -> str:
    """
    Find the strongest champions based on total power (attack + defense + health).
    
    Args:
        limit: Number of top champions to return (default: 10, max: 50)
        
    Returns:
        str: JSON formatted list of strongest champions with analysis
    """
    try:
        # Validate and cap limit
        limit = min(max(1, limit), 50)
        
        # Query for strongest champions
        query = """
        SELECT ge.id, ge.name, ge.entity_type, ge.rarity, ge.affinity, ge.class_type, ge.faction,
               es.attack, es.defense, es.health, es.speed,
               (es.attack + es.defense + es.health) as total_power
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE ge.entity_type = 'champion'
        ORDER BY total_power DESC
        LIMIT ?
        """
        
        champions = execute_query(query, (limit,))
        
        if not champions:
            return json.dumps({
                "status": "error",
                "message": "No champions found in database",
                "champions": [],
                "count": 0,
                "internal_info": {
                    "function_name": "gcs_find_strongest_champions",
                    "parameters": {"limit": limit}
                }
            })
        
        # Calculate statistics
        powers = [c['total_power'] for c in champions]
        highest_power = max(powers)
        lowest_power = min(powers)
        average_power = sum(powers) / len(powers)
        power_range = highest_power - lowest_power
        
        # Distribution analysis
        distribution = {
            'by_affinity': {},
            'by_class': {},
            'by_rarity': {}
        }
        
        for champion in champions:
            # Count by affinity
            affinity = champion.get('affinity', 'unknown')
            distribution['by_affinity'][affinity] = distribution['by_affinity'].get(affinity, 0) + 1
            
            # Count by class
            class_type = champion.get('class_type', 'unknown')
            distribution['by_class'][class_type] = distribution['by_class'].get(class_type, 0) + 1
            
            # Count by rarity
            rarity = champion.get('rarity', 'unknown')
            distribution['by_rarity'][rarity] = distribution['by_rarity'].get(rarity, 0) + 1
        
        # Get top champion details
        top_champion = champions[0] if champions else None
        
        # Create summary
        summary_parts = [f"Top {len(champions)} strongest champions"]
        if top_champion:
            summary_parts.append(f"{top_champion['name']} leads with {top_champion['total_power']} power")
        summary_parts.append(f"Average power: {average_power:.1f}")
        summary = ". ".join(summary_parts)
        
        # Create formatted list for LLM presentation
        champion_list = []
        for i, champion in enumerate(champions, 1):
            champion_list.append(f"{i}. **{champion['name']}** - Power: {champion['total_power']} ({champion.get('rarity', 'N/A')} {champion.get('affinity', 'N/A')} {champion.get('class_type', 'N/A')})")
        
        formatted_list = "\n".join(champion_list)
        
        return json.dumps({
            "status": "success",
            "message": f"Found {len(champions)} strongest champions",
            "analysis_type": "strongest_champions",
            "entity_type": "champion",
            "champions": champions,
            "count": len(champions),
            "requested_limit": limit,
            "power_stats": {
                "highest": highest_power,
                "lowest": lowest_power,
                "average": round(average_power, 1),
                "range": power_range
            },
            "distribution": distribution,
            "top_champion": {
                "name": top_champion['name'],
                "id": top_champion['id'],
                "power": top_champion['total_power'],
                "rarity": top_champion.get('rarity'),
                "affinity": top_champion.get('affinity'),
                "class_type": top_champion.get('class_type')
            } if top_champion else None,
            "summary": summary,
            "formatted_list": formatted_list,
            "llm_instruction": f"Present the following list of {len(champions)} strongest champions to the user:\n\n{formatted_list}\n\nThen provide a brief summary of the power statistics and distribution.",
            "internal_info": {
                "function_name": "gcs_find_strongest_champions",
                "parameters": {"limit": limit}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in gcs_find_strongest_champions: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error finding strongest champions: {str(e)}",
            "champions": [],
            "count": 0,
            "internal_info": {
                "function_name": "gcs_find_strongest_champions",
                "parameters": {"limit": limit}
            }
        })