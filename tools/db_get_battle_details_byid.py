#!/usr/bin/env python3
"""
Get Battle Details By ID
Retrieves detailed battle information by battle ID from PostgreSQL database
"""

import logging

# Import the global PostgreSQL connection
from db_postgres import execute_query

# Logger
logger = logging.getLogger("BattleDetailsById")


def db_get_battle_details_byid(battle_id: str) -> dict:
    """
    Get detailed information about a specific battle by battle_id from PostgreSQL database
    
    Args:
        battle_id (str): Battle ID to search for (exact match)
        
    Returns:
        str: JSON formatted battle details response with summary_json
    """
    try:
        logger.info(f"Querying PostgreSQL for battle details by ID: {battle_id}")
        
        # Search for battle by exact battle_id
        results = execute_query("""
            SELECT battle_id, battle_name, summary_text, summary_json
            FROM battle_details 
            WHERE battle_id = %s
        """, (battle_id,))
        
        if not results:
            return {
                "status": "error",
                "message": f"No battle found with ID '{battle_id}'",
                "battle_id": battle_id,
                "internal_info": {
                    "function_name": "db_get_battle_details_byid",
                    "parameters": {"battle_id": battle_id}
                }
            }
        
        # Single battle found (battle_id should be unique)
        battle = results[0]
        
        # Prepare battle details using summary_json as primary data
        battle_details = {
            "battle_id": battle["battle_id"],
            "battle_name": battle["battle_name"],
            "summary_text": battle["summary_text"] or "No summary available",
            "summary_json": battle["summary_json"] if battle["summary_json"] else {}
        }
        
        return {
            "status": "success",
            "message": f"Battle details retrieved for ID '{battle_id}'",
            "battle_id": battle_id,
            "battle_name": battle["battle_name"],
            "battle_details": battle_details,
            "data_source": "PostgreSQL battle_details table",
            "llm_cache_duration": 5,
            "internal_info": {
                "function_name": "db_get_battle_details_byid",
                "parameters": {"battle_id": battle_id}
            }
        }
            
    except Exception as e:
        logger.error(f"Error getting battle details by ID '{battle_id}': {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": f"Database error while retrieving battle details for ID '{battle_id}': {str(e)}",
            "battle_id": battle_id,
            "internal_info": {
                "function_name": "db_get_battle_details_byid",
                "parameters": {"battle_id": battle_id},
                "error": str(e)
            }
        }