#!/usr/bin/env python3
"""
Tool: Get random greetings from database
Fetch a random greeting from the greetings database
"""

import json
import os
import sqlite3
import logging

# Logger
logger = logging.getLogger("DB Get Random Greetings")


def db_get_random_greetings() -> str:
    """
    Get a random greeting from the greetings database (OpenAI Function Calling format)
    
    Returns:
        str: JSON formatted greeting response
    """
    try:
        # Connect to greetings database from WORKLOAD_DB_PATH
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "greetings.db.sqlite")
        
        logger.info(f"Connecting to greetings database at: {db_path}")
        conn = sqlite3.connect(db_path)
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT greeting 
                FROM greeting_records 
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            
            if result:
                greeting = result[0]
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
                
        finally:
            conn.close()
            
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