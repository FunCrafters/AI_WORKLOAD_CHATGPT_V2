#!/usr/bin/env python3
import logging

# Import the global PostgreSQL connection
from db_postgres import execute_query

# Logger
logger = logging.getLogger("ChampionDetailsById")


def db_get_champion_details_byid(champion_id: str) -> dict:
    """
    Get detailed information about a specific champion by champion_id from PostgreSQL database

    Args:
        champion_id (str): Champion ID to search for (exact match)

    Returns:
        str: JSON formatted champion details response with summary_json
    """
    try:
        logger.info(f"Querying PostgreSQL for champion details by ID: {champion_id}")

        # Search for champion by exact champion_id
        results = execute_query(
            """
            SELECT champion_id, champion_name, summary_text, summary_json
            FROM champion_details 
            WHERE champion_id = %s
        """,
            (champion_id,),
        )

        if not results:
            return {
                "status": "error",
                "message": f"No champion found with ID '{champion_id}'",
                "champion_id": champion_id,
                "internal_info": {
                    "function_name": "db_get_champion_details_byid",
                    "parameters": {"champion_id": champion_id},
                },
            }

        # Single champion found (champion_id should be unique)
        champion = results[0]

        # Prepare champion details using summary_json as primary data
        champion_details = {
            "champion_id": champion["champion_id"],
            "champion_name": champion["champion_name"],
            "summary_text": champion["summary_text"] or "No summary available",
            "summary_json": champion["summary_json"]
            if champion["summary_json"]
            else {},
        }

        return {
            "status": "success",
            "message": f"Champion details retrieved for ID '{champion_id}'",
            "champion_id": champion_id,
            "champion_name": champion["champion_name"],
            "champion_details": champion_details,
            "data_source": "PostgreSQL champion_details table",
            "llm_cache_duration": 5,
            "internal_info": {
                "function_name": "db_get_champion_details_byid",
                "parameters": {"champion_id": champion_id},
            },
        }

    except Exception as e:
        logger.error(f"Error getting champion details by ID '{champion_id}': {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": f"Database error while retrieving champion details for ID '{champion_id}': {str(e)}",
            "champion_id": champion_id,
            "internal_info": {
                "function_name": "db_get_champion_details_byid",
                "parameters": {"champion_id": champion_id},
                "error": str(e),
            },
        }
