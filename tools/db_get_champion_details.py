#!/usr/bin/env python3
"""
Get Champion Details
Retrieves detailed champion information from PostgreSQL database
"""
import logging
import json

# Import the global PostgreSQL connection
from db_postgres import execute_query

# Logger
logger = logging.getLogger("Workload Tools")


def db_get_champion_details(champion_name: str) -> str:
    """
    Get detailed information about a specific champion from PostgreSQL database
    
    Args:
        champion_name (str): Champion name or partial name to search for (case insensitive)
        
    Returns:
        str: JSON formatted champion details response
    """
    try:
        logger.info(f"Querying PostgreSQL for champion details: {champion_name}")
        
        # Search for champions by name (case insensitive)
        results = execute_query("""
            SELECT champion_id, champion_name, summary_text, summary_json
            FROM champion_details 
            WHERE LOWER(champion_name) LIKE LOWER(%s)
            ORDER BY champion_name
        """, (f"%{champion_name}%",))
        
        if not results:
            return json.dumps({
                "status": "error",
                "message": f"No champions found matching '{champion_name}'",
                "champion_name": champion_name,
                "champions": [],
                "internal_info": {
                    "function_name": "db_get_champion_details",
                    "parameters": {"champion_name": champion_name}
                }
            })
        
        if len(results) == 1:
            # Single champion found - return full details
            champion = results[0]
            
            # Prepare champion details using summary_text
            champion_details = {
                "champion_id": champion["champion_id"],
                "champion_name": champion["champion_name"],
                "summary_text": champion["summary_text"] or "No summary available",
                "summary_json": champion["summary_json"] if champion["summary_json"] else {}
            }
            
            return json.dumps({
                "status": "success",
                "message": f"Champion details retrieved for '{champion['champion_name']}'",
                "champion_name": champion["champion_name"],
                "champion_details": champion_details,
                "llm_cache_duration": 3,
                "internal_info": {
                    "function_name": "db_get_champion_details",
                    "parameters": {"champion_name": champion_name}
                }
            })
        else:
            # Multiple champions found - return list
            champions_list = []
            for champion in results:
                champions_list.append({
                    "champion_id": champion["champion_id"],
                    "champion_name": champion["champion_name"]
                })
            
            return json.dumps({
                "status": "success",
                "message": f"Found {len(results)} champions matching '{champion_name}'",
                "champion_name": champion_name,
                "multiple_champions": champions_list,
                "total_found": len(results),
                "guidance": "Multiple champions found. Use db_get_champion_details with specific champion name for detailed analysis.",
                "internal_info": {
                    "function_name": "db_get_champion_details",
                    "parameters": {"champion_name": champion_name}
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting champion details for '{champion_name}': {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return json.dumps({
            "status": "error",
            "message": f"Database error while retrieving champion details for '{champion_name}': {str(e)}",
            "champion_name": champion_name,
            "internal_info": {
                "function_name": "db_get_champion_details",
                "parameters": {"champion_name": champion_name},
                "error": str(e)
            }
        })

