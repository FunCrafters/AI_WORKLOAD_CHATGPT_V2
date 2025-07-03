#!/usr/bin/env python3
"""
Cache tool: Get bosses list
Returns list of all bosses from cache
"""

import json


def cache_get_bosses_list() -> str:
    """Returns list of all bosses in JSON format for OpenAI Function Calling"""
    # Import here to get current value, not cached import
    from workload_game_cache import BOSSES_LIST
    
    if not BOSSES_LIST:
        return json.dumps({
            "status": "error",
            "message": "No bosses data available. Cache may not be initialized.",
            "bosses": [],
            "internal_info": {
                "function_name": "cache_get_bosses_list",
                "parameters": {}
            }
        })
    
    return json.dumps({
        "status": "success",
        "message": f"Found {len(BOSSES_LIST)} bosses in database",
        "bosses": BOSSES_LIST,
        "internal_info": {
            "function_name": "cache_get_bosses_list",
            "parameters": {}
        }
    })


def cache_get_bosses_list_text() -> str:
    """Returns bosses list as text format for use in prompt building"""
    # Import here to get current value, not cached import
    from workload_game_cache import BOSSES_LIST
    
    if not BOSSES_LIST:
        return "No bosses data available. Cache may not be initialized."
    return f"{', '.join(BOSSES_LIST)}"