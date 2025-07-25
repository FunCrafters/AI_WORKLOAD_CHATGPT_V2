#!/usr/bin/env python3
"""
Get UX Details
Retrieves UX information from the ux database
"""

import logging

from session import Session

# Logger
logger = logging.getLogger("UXDetails")


def db_get_screen_details(query: str, session: Session) -> dict:
    gamestate = session.game_state

    if gamestate is None:
        return {
            "status": "error",
            "message": "Game state is not available",
        }

    try:
        result = gamestate.get_details(query)

        if result:
            return {
                "status": "success",
                "message": f"Details for '{query}' element",
                "content": {"details": result},
            }
        else:
            logger.warning(f"No details found for '{query}'")
            return {
                "status": "error",
                "message": f"No details found for '{query}'",
                "content": {"details": ""},
            }
    except Exception as e:
        logger.error(f"Error retrieving screen details for '{query}': {e}")
        return {"status": "error", "message": f"Error retrieving screen details: {str(e)}", "content": ""}
