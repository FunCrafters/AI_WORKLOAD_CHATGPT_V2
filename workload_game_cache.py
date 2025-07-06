#!/usr/bin/env python3
"""
Workload Game Cache
Game data cache and static data functions
"""

import logging
from typing import Dict, List, Optional
from tools.db_rag_get_smalltalk import db_get_smalltalk_text

# Logger
logger = logging.getLogger("Workload Game Cache")

#######################
# Global variables for game data cache
#######################

# JSON data tracking (still needed)
CURRENT_JSON_DATA = None
HAS_SCREEN_DATA = False




def set_current_json_data(json_data: dict) -> None:   #todo - to jest jakis syf, do pełnej refaktoryzacji
    """
    Set current JSON data and check for screenData presence
    
    Args:
        json_data: JSON data to analyze
    """
    global CURRENT_JSON_DATA, HAS_SCREEN_DATA
    
    CURRENT_JSON_DATA = json_data
    HAS_SCREEN_DATA = bool(json_data and json_data.get("screenData"))
    
    logger.info(f"JSON data updated. ScreenData present: {HAS_SCREEN_DATA}")


#######################
# Cache Info Function
#######################

def get_cache_info() -> str:
    """
    Get detailed information about all initialized caches
    
    Returns:
        str: Detailed cache information including contents and statistics
    """
    cache_info = []
    
    # JSON data status
    cache_info.append("### JSON DATA STATUS")
    cache_info.append(f"📄 JSON Data Loaded: {'Yes' if CURRENT_JSON_DATA else 'No'}")
    cache_info.append(f"🖥️  ScreenData Present: {'Yes' if HAS_SCREEN_DATA else 'No'}")
    cache_info.append(f"🛠️  Screen Context Tool: {'Available' if HAS_SCREEN_DATA else 'Unavailable'}")
    
    cache_info.append("")
    
    return "\n".join(cache_info)
