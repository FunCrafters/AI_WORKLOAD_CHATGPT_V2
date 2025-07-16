#!/usr/bin/env python3
"""
Get Lore Details
Retrieves lore information from the lore database
"""

import os
import logging
import json
from typing import Optional

# Import the global PostgreSQL connection
from db_postgres import execute_query

# Logger
logger = logging.getLogger("LoreDetails")


def _create_error_response(action: str, message: str, error_details: str, champion_name: str) -> str:
    """Helper function to create consistent error responses"""
    return json.dumps({
        "status": "error",
        "action": action,
        "message": message,
        "error_details": error_details,
        "internal_info": {
            "function_name": "db_get_lore_details",
            "parameters": {"champion_name": champion_name}
        }
    })


def db_get_lore_details(champion_name: str) -> str:
    """
    Get champion lore report from the lore database
    
    Args:
        champion_name (str): Name of the champion to get lore for (case insensitive)
        
    Returns:
        Formatted string with champion lore report
    """
    try:
        logger.info(f"Querying PostgreSQL for lore details: {champion_name}")
        
        # Search for champion by name (case insensitive)
        results = execute_query("""
            SELECT champion_id, champion_name, lore_text 
            FROM lore_records 
            WHERE LOWER(champion_name) LIKE LOWER(%s)
        """, (f"%{champion_name}%",))
        
        result = results[0] if results else None
        
        if result:
            # Format the lore report as a string (result is already a dictionary)
            report = f"""# CHAMPION LORE REPORT

**Champion:** {result["champion_name"]}

{result["lore_text"]}

---
*Report generated from Mandalorian Archives - Report Database*"""
            
            # Return JSON with report data and instruction for LLM
            return json.dumps({
                "status": "success",
                "action": "DISPLAY_REPORT_FINAL",
                "message": "Champion lore report retrieved successfully",
                "report_data": {
                    "champion_name": result["champion_name"],
                    "champion_id": result["champion_id"],
                    "formatted_report": report
                },
                "llm_cache_duration": 3,
                "internal_info": {
                    "function_name": "db_get_lore_details",
                    "parameters": {"champion_name": champion_name}
                }
            })
        else:
            return _create_error_response(
                "REPORT_NOT_FOUND",
                f"No lore found for champion: {champion_name}",
                f"The champion '{champion_name}' was not found in the lore database. Please check the spelling or try a different name.",
                champion_name
            )
            
    except Exception as e:
        logger.error(f"Error getting champion report for '{champion_name}': {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return _create_error_response(
            "DATABASE_ERROR",
            f"Database error while retrieving lore for '{champion_name}'",
            str(e),
            champion_name
        )

