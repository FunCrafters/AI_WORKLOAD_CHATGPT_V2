#!/usr/bin/env python3
"""
Get UX Details
Retrieves UX information from the ux database
"""

import os
import sqlite3
import logging
import json
from typing import Optional

# Logger
logger = logging.getLogger("Workload Tools")


def _create_error_response(action: str, message: str, error_details: str, query: str) -> str:
    """Helper function to create consistent error responses"""
    return json.dumps({
        "status": "error",
        "action": action,
        "message": message,
        "error_details": error_details,
        "internal_info": {
            "function_name": "db_get_ux_details",
            "parameters": {"query": query}
        }
    })


def db_get_ux_details(query: str) -> str:
    """
    Get UX information from the ux database
    
    Args:
        query (str): Search query for UX information (case insensitive)
        
    Returns:
        Formatted string with UX details
    """
    try:
        # Get database path from environment
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/root/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "ux.db.sqlite")
        
        logger.info(f"Opening ux database connection: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Search for UX information by name (case insensitive)
        cursor.execute("""
            SELECT ux_id, ux_name, ux_content 
            FROM ux_records 
            WHERE LOWER(ux_id) LIKE LOWER(?)
            ORDER BY ux_name
            LIMIT 10
        """, (f"%{query}%",))
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            # Format results
            ux_results = []
            for result in results:
                ux_results.append({
                    "ux_id": result["ux_id"],
                    "ux_name": result["ux_name"],
                    "ux_content": result["ux_content"]
                })
            
            # Return JSON with UX data
            return json.dumps({
                "status": "success",
                "message": f"Found {len(ux_results)} UX result(s) for '{query}'",
                "search_query": query,
                "category": "ux",
                "content": {
                    "results": ux_results,
                    "total_results": len(ux_results)
                },
                "llm_cache_duration": 3,
                "internal_info": {
                    "function_name": "db_get_ux_details",
                    "parameters": {"query": query}
                }
            })
        else:
            return _create_error_response(
                "UX_NOT_FOUND",
                f"No UX information found for query: {query}",
                f"The query '{query}' did not match any UX records. Try a different search term.",
                query
            )
            
    except Exception as e:
        logger.error(f"Error getting UX details for '{query}': {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return _create_error_response(
            "DATABASE_ERROR",
            f"Database error while retrieving UX information for '{query}'",
            str(e),
            query
        )

