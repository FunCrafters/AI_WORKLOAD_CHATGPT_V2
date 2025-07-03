#!/usr/bin/env python3
"""
Cache tool: Get champions list
Returns list of all champions from cache
"""

import json


def cache_get_champions_list() -> str:
    """Returns list of all champions in JSON format for OpenAI Function Calling"""
    # Import here to get current value, not cached import
    from workload_game_cache import CHAMPIONS_LIST
    
    if not CHAMPIONS_LIST:
        return json.dumps({
            "status": "error",
            "message": "No champions data available. Cache may not be initialized.",
            "champions": [],
            "internal_info": {
                "function_name": "cache_get_champions_list",
                "parameters": {}
            }
        })
    
    return json.dumps({
        "status": "success",
        "message": f"Found {len(CHAMPIONS_LIST)} champions in database",
        "champions": CHAMPIONS_LIST,
        "internal_info": {
            "function_name": "cache_get_champions_list",
            "parameters": {}
        }
    })


def cache_get_champions_list_text() -> str:
    """Returns champions list as text format for use in prompt building"""
    # Import here to get current value, not cached import
    from workload_game_cache import CHAMPIONS_LIST
    
    if not CHAMPIONS_LIST:
        return "No champions data available. Cache may not be initialized."
    return f"{', '.join(CHAMPIONS_LIST)}"