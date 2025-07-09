#!/usr/bin/env python3
"""
PostgreSQL Database Tool: Find Strongest Champions
Find the strongest champions based on total power with optional trait filtering
"""

import json
import logging
from db_postgres import execute_query

# Logger
logger = logging.getLogger("ChampComparator")


def db_find_strongest_champions(limit: int = 10, rarity: str|None = None, affinity: str|None = None, class_type: str|None = None) -> str:
    """
    Find the strongest champions based on total power (attack + defense + health) with optional trait filtering.
    
    Args:
        limit: Number of top champions to return (default: 10, max: 50)
        rarity: Filter by rarity (legendary, epic, rare, uncommon, common)
        affinity: Filter by affinity (red, blue, green, yellow, purple)
        class_type: Filter by class type (attacker, defender, support)
        
    Returns:
        str: JSON formatted list of strongest champions with analysis
    """
    try:
        # Validate and cap limit
        limit = min(max(1, limit), 50)
        
        # Build query conditions
        conditions = ["ct.champion_name IS NOT NULL"]
        params = []
        
        # Add trait filtering if provided
        if rarity:
            conditions.append("ct.rarity = %s")
            params.append(rarity.upper())
            
        if affinity:
            conditions.append("ct.affinity = %s")
            params.append(affinity.upper())
            
        if class_type:
            conditions.append("ct.class = %s")
            params.append(class_type.upper())
        
        # Add limit parameter
        params.append(limit)
        
        # Build query
        query = f"""
        SELECT ct.id, ct.champion_name, ct.rarity, ct.affinity, ct.class, ct.faction,
               cs.attack, cs.defense, cs.health, cs.speed,
               (cs.attack + cs.defense + cs.health) as total_power
        FROM champion_traits ct
        JOIN champion_stats cs ON ct.champion_name = cs.champion_name
        WHERE {' AND '.join(conditions)}
        ORDER BY total_power DESC
        LIMIT %s
        """
        
        champions = execute_query(query, params)
        
        if not champions:
            trait_filters = []
            if rarity:
                trait_filters.append(f"rarity={rarity}")
            if affinity:
                trait_filters.append(f"affinity={affinity}")
            if class_type:
                trait_filters.append(f"class_type={class_type}")
            
            filter_text = f" matching {', '.join(trait_filters)}" if trait_filters else ""
            no_results_message = f"No champions found{filter_text}"
            
            return json.dumps({
                "status": "success",
                "message": no_results_message,
                "champions": [],
                "count": 0,
                "filters": {
                    "rarity": rarity,
                    "affinity": affinity,
                    "class_type": class_type
                },
                "power_stats": {},
                "distribution": {"by_affinity": {}, "by_class": {}, "by_rarity": {}},
                "top_champion": None,
                "summary": no_results_message,
                "formatted_list": f"No champions found{filter_text}.",
                "llm_instruction": f"No champions found{filter_text}. Suggest trying different criteria or removing some filters.",
                "internal_info": {
                    "function_name": "db_find_strongest_champions",
                    "parameters": {"limit": limit, "rarity": rarity, "affinity": affinity, "class_type": class_type}
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
            affinity_val = champion.get('affinity', 'unknown')
            distribution['by_affinity'][affinity_val] = distribution['by_affinity'].get(affinity_val, 0) + 1
            
            # Count by class
            class_val = champion.get('class', 'unknown')
            distribution['by_class'][class_val] = distribution['by_class'].get(class_val, 0) + 1
            
            # Count by rarity
            rarity_val = champion.get('rarity', 'unknown')
            distribution['by_rarity'][rarity_val] = distribution['by_rarity'].get(rarity_val, 0) + 1
        
        # Get top champion details
        top_champion = champions[0] if champions else None
        
        # Create filter description
        trait_filters = []
        if rarity:
            trait_filters.append(f"rarity={rarity}")
        if affinity:
            trait_filters.append(f"affinity={affinity}")
        if class_type:
            trait_filters.append(f"class_type={class_type}")
        
        filter_text = f" matching {', '.join(trait_filters)}" if trait_filters else ""
        
        # Create summary
        summary_parts = [f"Top {len(champions)} strongest champions{filter_text}"]
        if top_champion:
            summary_parts.append(f"{top_champion['champion_name']} leads with {top_champion['total_power']} power")
        summary_parts.append(f"Average power: {average_power:.1f}")
        summary = ". ".join(summary_parts)
        
        # Create formatted list for LLM presentation
        champion_list = []
        for i, champion in enumerate(champions, 1):
            champion_list.append(f"{i}. **{champion['champion_name']}** - Power: {champion['total_power']} ({champion.get('rarity', 'N/A')} {champion.get('affinity', 'N/A')} {champion.get('class', 'N/A')})")
        
        formatted_list = "\n".join(champion_list)
        
        return json.dumps({
            "status": "success",
            "message": f"Found {len(champions)} strongest champions{filter_text}",
            "analysis_type": "strongest_champions",
            "entity_type": "champion",
            "champions": champions,
            "count": len(champions),
            "requested_limit": limit,
            "filters": {
                "rarity": rarity,
                "affinity": affinity,
                "class_type": class_type
            },
            "power_stats": {
                "highest": highest_power,
                "lowest": lowest_power,
                "average": round(average_power, 1),
                "range": power_range
            },
            "distribution": distribution,
            "top_champion": {
                "name": top_champion['champion_name'],
                "id": top_champion['id'],
                "power": top_champion['total_power'],
                "rarity": top_champion.get('rarity'),
                "affinity": top_champion.get('affinity'),
                "class_type": top_champion.get('class')
            } if top_champion else None,
            "summary": summary,
            "formatted_list": formatted_list,
            "llm_instruction": f"Present the following list of {len(champions)} strongest champions{filter_text} to the user:\n\n{formatted_list}\n\nThen provide a brief summary of the power statistics and distribution.",
            "internal_info": {
                "function_name": "db_find_strongest_champions",
                "parameters": {"limit": limit, "rarity": rarity, "affinity": affinity, "class_type": class_type}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in db_find_strongest_champions: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error finding strongest champions: {str(e)}",
            "champions": [],
            "count": 0,
            "filters": {
                "rarity": rarity,
                "affinity": affinity,
                "class_type": class_type
            },
            "internal_info": {
                "function_name": "db_find_strongest_champions",
                "parameters": {"limit": limit, "rarity": rarity, "affinity": affinity, "class_type": class_type}
            }
        })