#!/usr/bin/env python3
"""
GCS Tool: Get Champions by Traits
Find champions that match specified traits (rarity, affinity, class, etc.)
"""

import json
import logging
from db_gcs import execute_query

# Logger
logger = logging.getLogger("GCS Get Champions by Traits")


def gcs_get_champions_by_traits(traits: list, limit: int = 50) -> str:
    """
    Find champions that match all specified traits.
    
    Args:
        traits: List of trait values to filter by (e.g., ['legendary', 'red', 'attacker'])
        limit: Maximum number of results to return (default: 50, max: 100)
        
    Returns:
        str: JSON formatted list of champions matching the specified traits
    """
    try:
        # Validate and cap limit
        limit = min(max(1, limit), 100)
        
        # Define trait categories
        trait_categories = {
            'rarity': ['legendary', 'epic', 'rare', 'uncommon', 'common'],
            'affinity': ['red', 'blue', 'green', 'yellow', 'purple'],
            'class_type': ['attacker', 'defender', 'support']
        }
        
        if not traits:
            return json.dumps({
                "status": "error",
                "message": "At least one trait must be specified",
                "traits": [],
                "champions": [],
                "available_traits": trait_categories,
                "internal_info": {
                    "function_name": "gcs_get_champions_by_traits",
                    "parameters": {"traits": traits, "limit": limit}
                }
            })
        
        # Categorize input traits and validate
        trait_filters = {}
        unrecognized_traits = []
        
        for trait in traits:
            trait_lower = trait.lower()
            found = False
            
            for category, values in trait_categories.items():
                if trait_lower in values:
                    trait_filters[category] = trait_lower
                    found = True
                    break
            
            if not found:
                unrecognized_traits.append(trait)
        
        # If no recognized traits, return error
        if not trait_filters:
            return json.dumps({
                "status": "error",
                "message": f"No recognized traits found. Unrecognized: {', '.join(unrecognized_traits)}",
                "traits": traits,
                "champions": [],
                "available_traits": trait_categories,
                "internal_info": {
                    "function_name": "gcs_get_champions_by_traits",
                    "parameters": {"traits": traits, "limit": limit}
                }
            })
        
        # Build dynamic query based on specified traits
        query_conditions = ["ge.entity_type = 'champion'"]
        query_params = []
        
        for category, value in trait_filters.items():
            query_conditions.append(f"ge.{category} = ?")
            query_params.append(value)
        
        query = f"""
        SELECT ge.id, ge.name, ge.entity_type, ge.rarity, ge.affinity, ge.class_type, 
               ge.faction, ge.series,
               es.attack, es.defense, es.health, es.speed,
               (es.attack + es.defense + es.health) as total_power
        FROM game_entities ge
        JOIN entity_stats es ON ge.id = es.entity_id
        WHERE {' AND '.join(query_conditions)}
        ORDER BY total_power DESC
        LIMIT ?
        """
        
        query_params.append(limit)
        champions = execute_query(query, query_params)
        
        if not champions:
            recognized_traits = list(trait_filters.values())
            no_results_message = f"No champions found matching traits: {', '.join(recognized_traits)}"
            llm_no_results = f"No champions found matching the traits: {', '.join(recognized_traits)}. Suggest trying different trait combinations."
            
            if unrecognized_traits:
                no_results_message += f" For other traits like {', '.join(unrecognized_traits)}, use other specialized functions."
                llm_no_results += f" For additional traits like {', '.join(unrecognized_traits)}, consider using other search functions."
            
            return json.dumps({
                "status": "success",
                "message": no_results_message,
                "traits": traits,
                "recognized_traits": recognized_traits,
                "unrecognized_traits": unrecognized_traits,
                "champions": [],
                "count": 0,
                "power_stats": {},
                "strongest": None,
                "summary": no_results_message,
                "formatted_list": "No champions found with the specified traits.",
                "llm_instruction": llm_no_results,
                "available_traits": trait_categories,
                "internal_info": {
                    "function_name": "gcs_get_champions_by_traits",
                    "parameters": {"traits": traits, "limit": limit}
                }
            })
        
        # Calculate power statistics
        powers = [c['total_power'] for c in champions]
        highest_power = max(powers)
        lowest_power = min(powers)
        average_power = sum(powers) / len(powers)
        
        strongest_champion = champions[0]  # Already sorted by total_power DESC
        
        power_stats = {
            "highest": highest_power,
            "lowest": lowest_power,
            "average": round(average_power, 1)
        }
        
        # Create formatted list for LLM presentation
        champion_list = []
        for i, champion in enumerate(champions, 1):
            champion_list.append(
                f"{i}. **{champion['name']}** - Power: {champion['total_power']} "
                f"({champion.get('rarity', 'N/A')} {champion.get('affinity', 'N/A')} "
                f"{champion.get('class_type', 'N/A')})"
            )
        
        formatted_list = "\n".join(champion_list)
        
        # Create summary
        recognized_traits = list(trait_filters.values())
        trait_list = ', '.join(recognized_traits)
        summary = (
            f"Found {len(champions)} champions matching traits: {trait_list}. "
            f"Strongest: {strongest_champion['name']} ({strongest_champion['total_power']} power)"
        )
        
        # Add note about other traits if any
        if unrecognized_traits:
            summary += f" For other traits like {', '.join(unrecognized_traits)}, use specialized functions."
        
        # Create LLM instruction
        llm_instruction = f"Present the list of {len(champions)} champions matching traits ({trait_list}):\n\n{formatted_list}\n\nHighlight that {strongest_champion['name']} is the strongest with {strongest_champion['total_power']} power."
        if unrecognized_traits:
            llm_instruction += f"\n\nFor additional traits like {', '.join(unrecognized_traits)}, recommend using other specialized search functions."
        
        return json.dumps({
            "status": "success",
            "message": summary,
            "traits": traits,
            "recognized_traits": recognized_traits,
            "unrecognized_traits": unrecognized_traits,
            "champions": champions,
            "count": len(champions),
            "requested_limit": limit,
            "power_stats": power_stats,
            "strongest": {
                "name": strongest_champion['name'],
                "id": strongest_champion['id'],
                "power": strongest_champion['total_power'],
                "rarity": strongest_champion.get('rarity'),
                "affinity": strongest_champion.get('affinity'),
                "class_type": strongest_champion.get('class_type')
            },
            "summary": summary,
            "formatted_list": formatted_list,
            "llm_instruction": llm_instruction,
            "available_traits": trait_categories,
            "internal_info": {
                "function_name": "gcs_get_champions_by_traits",
                "parameters": {"traits": traits, "limit": limit}
            }
        })
        
    except Exception as e:
        logger.error(f"Error in gcs_get_champions_by_traits: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching champions by traits: {str(e)}",
            "traits": traits,
            "champions": [],
            "internal_info": {
                "function_name": "gcs_get_champions_by_traits",
                "parameters": {"traits": traits, "limit": limit}
            }
        })