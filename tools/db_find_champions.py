#!/usr/bin/env python3
"""
PostgreSQL Database Tool: Find Champions
Search for champions by name with basic information from PostgreSQL database
"""

import json
import logging
from db_postgres import execute_query

# Logger
logger = logging.getLogger("ChampionsSearch")


def db_find_champions(name: str, limit: int = 20) -> dict:
    """
    Search for champions by name with basic information from PostgreSQL database.
    
    Args:
        name: Champion name or partial name to search for
        limit: Maximum number of champions to return (default: 20, max: 100)
        
    Returns:
        str: JSON formatted search results with champions list
    """
    try:
        # Validate limit parameter
        if limit < 1:
            limit = 20
        elif limit > 100:
            limit = 100
        
        # Search for champions by name using fuzzy search
        search_query = """
        SELECT champion_name, rarity, affinity, class, faction, era, fighting_style, race, side_of_force
        FROM champion_traits
        WHERE champion_name ILIKE %s
        ORDER BY champion_name
        LIMIT %s
        """
        
        search_param = f'%{name}%'
        search_results = execute_query(search_query, (search_param, limit))
        
        if not search_results:
            return {
                "status": "success",
                "message": f"No champions found matching '{name}'",
                "search_term": name,
                "champions": [],
                "total_found": 0,
                "llm_instruction": f"No champions found matching '{name}'. Please check the champion name and try again.",
                "internal_info": {
                    "function_name": "db_find_champions",
                    "parameters": {"name": name, "limit": limit}
                }
            }
        
        # Convert results to list of dictionaries
        champions = []
        for result in search_results:
            champions.append({
                "champion_name": result["champion_name"],
                "rarity": result["rarity"], 
                "affinity": result["affinity"],
                "class": result["class"],
                "faction": result["faction"],
                "era": result["era"],
                "fighting_style": result["fighting_style"],
                "race": result["race"],
                "side_of_force": result["side_of_force"]
            })
        
        return {
            "status": "success",
            "message": f"Found {len(champions)} champions matching '{name}'",
            "search_term": name,
            "total_found": len(champions),
            "champions": champions,
            "summary": f"Search results for '{name}': {len(champions)} champions found",
            "llm_instruction": f"Found {len(champions)} champions matching '{name}'. Present the list with basic traits information.",
            "internal_info": {
                "function_name": "db_find_champions",
                "parameters": {"name": name, "limit": limit}
            }
        }
        
    except Exception as e:
        logger.error(f"Error in db_find_champions: {str(e)}")
        return {
            "status": "error",
            "message": f"Error searching for champions: {str(e)}",
            "search_term": name,
            "champions": [],
            "total_found": 0,
            "internal_info": {
                "function_name": "db_find_champions",
                "parameters": {"name": name, "limit": limit}
            }
        }