#!/usr/bin/env python3
"""
Get Battle Details
Retrieves detailed battle information from PostgreSQL database
"""

import logging
import json

# Import the global PostgreSQL connection
from db_postgres import execute_query

# Logger
logger = logging.getLogger("BattleDetails")


def db_get_battle_details(battle_name: str) -> str:
    """
    Get detailed information about a specific battle from PostgreSQL database
    
    Args:
        battle_name (str): Battle name or partial name to search for (case insensitive)
        
    Returns:
        str: JSON formatted battle details response
    """
    try:
        logger.info(f"Querying PostgreSQL for battle details: {battle_name}")
        
        # Search for battles by name (case insensitive)
        results = execute_query("""
            SELECT battle_id, battle_name, summary_text, summary_json
            FROM battle_details 
            WHERE LOWER(battle_name) LIKE LOWER(%s)
            ORDER BY battle_name
        """, (f"%{battle_name}%",))
        
        if not results:
            return json.dumps({
                "status": "error",
                "message": f"No battles found matching '{battle_name}'",
                "battle_name": battle_name,
                "battles": [],
                "internal_info": {
                    "function_name": "db_get_battle_details",
                    "parameters": {"battle_name": battle_name}
                }
            })
        
        if len(results) == 1:
            # Single battle found - return full details
            battle = results[0]
            
            # Prepare battle details using summary_text
            battle_details = {
                "battle_id": battle["battle_id"],
                "battle_name": battle["battle_name"],
                "summary_text": battle["summary_text"] or "No summary available",
                "summary_json": battle["summary_json"] if battle["summary_json"] else {}
            }
            
            return json.dumps({
                "status": "success",
                "message": f"Battle details retrieved for '{battle['battle_name']}'",
                "battle_name": battle["battle_name"],
                "battle_details": battle_details,
                "data_source": "PostgreSQL battle_details table",
                "llm_cache_duration": 3,
                "internal_info": {
                    "function_name": "db_get_battle_details",
                    "parameters": {"battle_name": battle_name}
                }
            })
        else:
            # Multiple battles found - return list
            battles_list = []
            for battle in results:
                battles_list.append({
                    "battle_id": battle["battle_id"],
                    "battle_name": battle["battle_name"]
                })
            
            return json.dumps({
                "status": "success",
                "message": f"Found {len(results)} battles matching '{battle_name}'",
                "battle_name": battle_name,
                "multiple_battles": battles_list,
                "total_found": len(results),
                "guidance": "Multiple battles found. Use db_get_battle_details with specific battle name for detailed analysis.",
                "data_source": "PostgreSQL battle_details table",
                "internal_info": {
                    "function_name": "db_get_battle_details",
                    "parameters": {"battle_name": battle_name}
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting battle details for '{battle_name}': {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return json.dumps({
            "status": "error",
            "message": f"Database error while retrieving battle details for '{battle_name}': {str(e)}",
            "battle_name": battle_name,
            "internal_info": {
                "function_name": "db_get_battle_details",
                "parameters": {"battle_name": battle_name},
                "error": str(e)
            }
        })
