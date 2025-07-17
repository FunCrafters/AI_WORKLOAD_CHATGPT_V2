#!/usr/bin/env python3
"""
Get Screen Context Help
Get contextual help based on current screen and user question
"""

import json
import logging
from .db_get_ux_details import db_get_ux_details

# Logger
logger = logging.getLogger("ScreenContext")


def db_get_screen_context_help(user_question: str) -> dict:
    try:
        # Import here to get current values
        from workload_game_cache import HAS_SCREEN_DATA, CURRENT_JSON_DATA
        
        logger.info(f"🔍 db_get_screen_context_help called with question: '{user_question}'")
        
        # Single error check point
        if not HAS_SCREEN_DATA or not CURRENT_JSON_DATA:
            return _create_error_response(
                "No screen data available",
                user_question
            )
        
        logger.info(f"{CURRENT_JSON_DATA}")

        # Simple screen extraction like analyze_screen_context
        screen_data = CURRENT_JSON_DATA.get("screenData", {})
        screen_name = screen_data.get("Screen", "")
        
        if not screen_name:
            return _create_error_response(
                "No Screen field found in screenData",
                user_question
            )
        
        logger.info(f"✅ Found screen: {screen_name}")
        
        # Get UX details for the screen
        screen_result_json = db_get_ux_details(screen_name)
        
        # Extract content from JSON response
        ux_content = _extract_ux_content(screen_result_json)
        
        # If no specific content found, try with user question
        if not ux_content:
            combined_query = f"{user_question} {screen_name}"
            logger.info(f"🔍 Trying combined query: '{combined_query}'")
            screen_result_json = db_get_ux_details(combined_query)
            ux_content = _extract_ux_content(screen_result_json)
        
        # Format response
        content_parts = [
            "=== SCREEN CONTEXT INFORMATION ===",
            f"Current Screen: {screen_name}",
            f"User Question: {user_question}",
            "",
            "=== RELEVANT INFORMATION ==="
        ]
        
        if ux_content:
            content_parts.append(ux_content)
        else:
            content_parts.append("No specific help information found for this screen.")
        
        content = "\n".join(content_parts)
        
        return {
            "status": "success",
            "message": f"Found screen context help for: {screen_name}",
            "user_question": user_question,
            "screen_name": screen_name,
            "content": content,
            "internal_info": {
                "function_name": "db_get_screen_context_help",
                "parameters": {"user_question": user_question}
            }
        }
        
    except Exception as e:
        logger.error(f"Error in screen context help: {str(e)}")
        return _create_error_response(
            f"Error retrieving screen context help: {str(e)}",
            user_question
        )


def _create_error_response(message: str, user_question: str) -> dict:
    """Single error response creator"""
    return {
        "status": "error",
        "message": message,
        "user_question": user_question,
        "content": "",
        "internal_info": {
            "function_name": "db_get_screen_context_help",
            "parameters": {"user_question": user_question}
        }
    }


def _extract_ux_content(result_data: dict) -> str:
    """Extract content from UX details JSON response"""
    
    if result_data.get("status") == "success" and "content" in result_data:
        if "results" in result_data["content"]:
            results = result_data["content"]["results"]
            return "\n\n".join([f"**{r['ux_name']}**\n{r['ux_content']}" for r in results])
        else:
            return str(result_data["content"])
    return ""  