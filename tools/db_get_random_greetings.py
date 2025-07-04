#!/usr/bin/env python3
"""
Tool: Get random greetings from database
Fetch a random greeting from the greetings database
"""

import json
import os
import logging

# Import the global PostgreSQL connection
from db_postgres import execute_query

# Logger
logger = logging.getLogger("DB Get Random Greetings")


def db_get_random_greetings() -> str:
    """
    Get a random greeting from the greetings database (OpenAI Function Calling format)
    
    Returns:
        str: JSON formatted greeting response
    """
    try:
        logger.info("Querying PostgreSQL for random greeting")
        
        # Get a random greeting from PostgreSQL
        results = execute_query("""
            SELECT greeting 
            FROM greeting_records 
            ORDER BY RANDOM() 
            LIMIT 1
        """)
        
        if results:
            greeting = results[0]["greeting"]
            logger.info(f"Selected greeting: {greeting}")
                
            return json.dumps({
                "status": "success",
                "message": "Random greeting retrieved successfully",
                "content": {
                    "greeting": greeting
                },
                "internal_info": {
                    "function_name": "db_get_random_greetings",
                    "parameters": {}
                }
            })
        else:
            logger.warning("No greetings found in database")
            return json.dumps({
                "status": "error",
                "message": "No greetings available in database",
                "content": {
                    "greeting": "Greetings, cadet. T-3RN at your service."
                },
                "internal_info": {
                    "function_name": "db_get_random_greetings",
                    "parameters": {},
                    "fallback": True
                }
            })
            
    except Exception as e:
        logger.error(f"Error in db_get_random_greetings: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving greeting: {str(e)}",
            "content": {
                "greeting": "Greetings, cadet. T-3RN at your service."
            },
            "internal_info": {
                "function_name": "get_random_greetings",
                "parameters": {},
                "error": str(e),
                "fallback": True
            }
        })


def db_get_random_greetings_text() -> str:
    """
    Get a random greeting (text format for backward compatibility)
    
    Returns:
        str: Greeting text only
    """
    json_result = db_get_random_greetings()
    
    try:
        result_dict = json.loads(json_result)
        return result_dict["content"]["greeting"]
    except:
        return "Greetings, cadet. T-3RN at your service."