#!/usr/bin/env python3
"""
Get Champions List
Retrieves list of all champions from PostgreSQL database
"""

import os
import logging
import json
from typing import Optional

# Import the global PostgreSQL connection
from db_postgres import execute_query

# Logger
logger = logging.getLogger("Workload Tools")


def db_get_champions_list() -> str:
    """
    Get complete list of all available champions from PostgreSQL database
    
    Returns:
        str: JSON formatted champions list response
    """
    try:
        logger.info("Querying PostgreSQL for champions list")
        
        # Get all champion names from PostgreSQL
        results = execute_query("""
            SELECT champion_name 
            FROM champions 
            WHERE champion_name IS NOT NULL
            ORDER BY champion_name
        """)
        
        if results:
            # Extract champion names from results
            champions = [result["champion_name"] for result in results]
            
            return json.dumps({
                "status": "success",
                "message": f"Found {len(champions)} champions in database",
                "champions": champions,
                "internal_info": {
                    "function_name": "db_get_champions_list",
                    "parameters": {}
                }
            })
        else:
            logger.warning("No champions found in database")
            return json.dumps({
                "status": "error",
                "message": "No champions data available in database",
                "champions": [],
                "internal_info": {
                    "function_name": "db_get_champions_list",
                    "parameters": {}
                }
            })
            
    except Exception as e:
        logger.error(f"Error getting champions list: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return json.dumps({
            "status": "error",
            "message": f"Database error while retrieving champions list: {str(e)}",
            "champions": [],
            "internal_info": {
                "function_name": "db_get_champions_list",
                "parameters": {},
                "error": str(e)
            }
        })


def db_get_champions_list_text() -> str:
    """
    Get champions list as text format for use in prompt building
    
    Returns:
        str: Comma-separated list of champion names
    """
    try:
        json_result = db_get_champions_list()
        result_dict = json.loads(json_result)
        
        if result_dict["status"] == "success":
            return ", ".join(result_dict["champions"])
        else:
            return "Champions list not available"
    except Exception as e:
        logger.error(f"Error getting champions list text: {str(e)}")
        return "Champions list not available"