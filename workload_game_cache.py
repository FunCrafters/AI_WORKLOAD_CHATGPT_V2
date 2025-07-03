#!/usr/bin/env python3
"""
Workload Game Cache
Game data cache and static data functions
"""

import logging
from typing import Dict, List, Optional
from db_smalltalk import initialize_smalltalk_db, get_random_smalltalk_topic_and_knowledge

# Logger
logger = logging.getLogger("Workload Game Cache")

#######################
# Global variables for game data cache
#######################

CHAMPIONS_LIST = []
BOSSES_LIST = []
RARITY_MAPPING = {}
CLASS_MAPPING = {}
AFFINITY_MAPPING = {}

# Alias mapping and JSON data tracking
ALIAS_TO_NAME_MAPPING = {}
CURRENT_JSON_DATA = None
HAS_SCREEN_DATA = False



#######################
# Game Data Cache Functions
#######################

def initialize_game_data_cache(vectorstore):
    """Initialize cache during application startup"""
    global CHAMPIONS_LIST, BOSSES_LIST, RARITY_MAPPING, CLASS_MAPPING, AFFINITY_MAPPING, ALIAS_TO_NAME_MAPPING
    
    try:
        results = vectorstore.get(include=["metadatas"])
        
        champions = set()
        bosses = set()
        rarity_map = {}
        class_map = {}
        affinity_map = {}
        alias_map = {}
        
        for metadata in results["metadatas"]:
            category = metadata.get("category", "")
            name = metadata.get("name", "")
            alias = metadata.get("alias", "")
            rarity = metadata.get("rarity", "")
            class_type = metadata.get("class", "")
            affinity = metadata.get("affinity", "")
            
            # Build alias mapping for UX category
            if category == "ux" and name and alias:
                alias_map[alias] = name
            
            if category == "champions" and name:
                champions.add(name)
                
                # Rarity mapping
                if rarity:
                    if rarity not in rarity_map:
                        rarity_map[rarity] = []
                    if name not in rarity_map[rarity]:
                        rarity_map[rarity].append(name)
                
                # Class mapping
                if class_type:
                    if class_type not in class_map:
                        class_map[class_type] = []
                    if name not in class_map[class_type]:
                        class_map[class_type].append(name)
                
                # Affinity mapping
                if affinity:
                    if affinity not in affinity_map:
                        affinity_map[affinity] = []
                    if name not in affinity_map[affinity]:
                        affinity_map[affinity].append(name)
                        
            elif category == "bosses" and name:
                bosses.add(name)
        
        CHAMPIONS_LIST = sorted(list(champions))
        BOSSES_LIST = sorted(list(bosses))
        RARITY_MAPPING = {k: sorted(v) for k, v in rarity_map.items()}
        CLASS_MAPPING = {k: sorted(v) for k, v in class_map.items()}
        AFFINITY_MAPPING = {k: sorted(v) for k, v in affinity_map.items()}
        ALIAS_TO_NAME_MAPPING = alias_map
        
        logger.info(f"Game data cache initialized: {len(CHAMPIONS_LIST)} champions, {len(BOSSES_LIST)} bosses")
        logger.info(f"Rarities: {list(RARITY_MAPPING.keys())}")
        logger.info(f"Classes: {list(CLASS_MAPPING.keys())}")
        logger.info(f"Affinities: {list(AFFINITY_MAPPING.keys())}")
        logger.info(f"Alias mappings: {len(ALIAS_TO_NAME_MAPPING)} UX aliases")
        
    except Exception as e:
        logger.error(f"Error initializing game data cache: {str(e)}")

# Smalltalk functions are now in db_smalltalk.py

# Re-export smalltalk functions for backward compatibility
# These are now imported from db_smalltalk.py at the top of the file

#######################
# Alias Mapping and JSON Data Functions
#######################

def get_name_from_alias(alias: str) -> str:
    """
    Get official name from alias
    
    Args:
        alias: Alias from JSON (e.g., 'ChampionFeatureModelsPresenter')
        
    Returns:
        str: Official name for user (e.g., 'Champion Card') or original alias if not found
    """
    return ALIAS_TO_NAME_MAPPING.get(alias, alias)

def set_current_json_data(json_data: dict) -> None:
    """
    Set current JSON data and check for screenData presence
    
    Args:
        json_data: JSON data to analyze
    """
    global CURRENT_JSON_DATA, HAS_SCREEN_DATA
    
    CURRENT_JSON_DATA = json_data
    HAS_SCREEN_DATA = bool(json_data and json_data.get("screenData"))
    
    logger.info(f"JSON data updated. ScreenData present: {HAS_SCREEN_DATA}")

def get_alias_mapping_info() -> str:
    """
    Get information about alias mapping for debugging
    
    Returns:
        str: Alias mapping information
    """
    if not ALIAS_TO_NAME_MAPPING:
        return "No alias mappings available. Cache may not be initialized."
    
    info = []
    info.append(f"Total alias mappings: {len(ALIAS_TO_NAME_MAPPING)}")
    info.append("\nSample mappings:")
    
    for i, (alias, name) in enumerate(ALIAS_TO_NAME_MAPPING.items()):
        if i >= 10:  # Show only first 10
            info.append(f"... and {len(ALIAS_TO_NAME_MAPPING) - 10} more")
            break
        info.append(f"  {alias} → {name}")
    
    return "\n".join(info)

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
    
    # Champions cache
    cache_info.append("### CHAMPIONS CACHE")
    if CHAMPIONS_LIST:
        cache_info.append(f"📊 Total Champions: {len(CHAMPIONS_LIST)}")
        cache_info.append(f"🎯 All Champions: {', '.join(CHAMPIONS_LIST)}")
    else:
        cache_info.append("❌ Champions cache is empty")
    
    cache_info.append("")
    
    # Bosses cache
    cache_info.append("### BOSSES CACHE")
    if BOSSES_LIST:
        cache_info.append(f"📊 Total Bosses: {len(BOSSES_LIST)}")
        cache_info.append(f"🎯 Sample Bosses: {', '.join(BOSSES_LIST[:10])}")
        if len(BOSSES_LIST) > 10:
            cache_info.append(f"   ... and {len(BOSSES_LIST) - 10} more")
    else:
        cache_info.append("❌ Bosses cache is empty")
    
    cache_info.append("")
    
    # Rarity mapping cache
    cache_info.append("### RARITY MAPPING CACHE")
    if RARITY_MAPPING:
        cache_info.append(f"📊 Total Rarity Categories: {len(RARITY_MAPPING)}")
        for rarity, champions in RARITY_MAPPING.items():
            cache_info.append(f"🔸 {rarity}: {len(champions)} champions")
            cache_info.append(f"   Sample: {', '.join(champions[:5])}")
            if len(champions) > 5:
                cache_info.append(f"   ... and {len(champions) - 5} more")
    else:
        cache_info.append("❌ Rarity mapping cache is empty")
    
    cache_info.append("")
    
    # Class mapping cache
    cache_info.append("### CLASS MAPPING CACHE")
    if CLASS_MAPPING:
        cache_info.append(f"📊 Total Class Categories: {len(CLASS_MAPPING)}")
        for class_name, champions in CLASS_MAPPING.items():
            cache_info.append(f"🔸 {class_name}: {len(champions)} champions")
            cache_info.append(f"   Sample: {', '.join(champions[:5])}")
            if len(champions) > 5:
                cache_info.append(f"   ... and {len(champions) - 5} more")
    else:
        cache_info.append("❌ Class mapping cache is empty")
    
    cache_info.append("")
    
    # Affinity mapping cache
    cache_info.append("### AFFINITY MAPPING CACHE")
    if AFFINITY_MAPPING:
        cache_info.append(f"📊 Total Affinity Categories: {len(AFFINITY_MAPPING)}")
        for affinity, champions in AFFINITY_MAPPING.items():
            cache_info.append(f"🔸 {affinity}: {len(champions)} champions")
            cache_info.append(f"   Sample: {', '.join(champions[:5])}")
            if len(champions) > 5:
                cache_info.append(f"   ... and {len(champions) - 5} more")
    else:
        cache_info.append("❌ Affinity mapping cache is empty")
    
    cache_info.append("")
    
    # Alias mapping cache
    cache_info.append("### ALIAS MAPPING CACHE")
    if ALIAS_TO_NAME_MAPPING:
        cache_info.append(f"📊 Total Alias Mappings: {len(ALIAS_TO_NAME_MAPPING)}")
        cache_info.append(f"🔸 Sample Mappings:")
        for i, (alias, name) in enumerate(list(ALIAS_TO_NAME_MAPPING.items())[:5]):
            cache_info.append(f"   {alias} → {name}")
        if len(ALIAS_TO_NAME_MAPPING) > 5:
            cache_info.append(f"   ... and {len(ALIAS_TO_NAME_MAPPING) - 5} more")
    else:
        cache_info.append("❌ Alias mapping cache is empty")
    
    cache_info.append("")
    
    # JSON data status
    cache_info.append("### JSON DATA STATUS")
    cache_info.append(f"📄 JSON Data Loaded: {'Yes' if CURRENT_JSON_DATA else 'No'}")
    cache_info.append(f"🖥️  ScreenData Present: {'Yes' if HAS_SCREEN_DATA else 'No'}")
    cache_info.append(f"🛠️  Screen Context Tool: {'Available' if HAS_SCREEN_DATA else 'Unavailable'}")
    
    cache_info.append("")
    
    # Smalltalk cache - get info from db_smalltalk module
    cache_info.append("### SMALLTALK TOPICS CACHE")
    try:
        from db_smalltalk import SMALLTALK_TOPICS, SMALLTALK_KNOWLEDGE
        if SMALLTALK_TOPICS:
            cache_info.append(f"📊 Total Smalltalk Topics: {len(SMALLTALK_TOPICS)}")
            cache_info.append(f"🎯 Sample Topics: {', '.join(SMALLTALK_TOPICS[:5])}")
            if len(SMALLTALK_TOPICS) > 5:
                cache_info.append(f"   ... and {len(SMALLTALK_TOPICS) - 5} more")
            # Calculate total knowledge size
            total_knowledge_chars = sum(len(k) for k in SMALLTALK_KNOWLEDGE.values())
            cache_info.append(f"📚 Total Knowledge Size: {total_knowledge_chars:,} characters")
        else:
            cache_info.append("❌ Smalltalk cache is empty")
    except ImportError:
        cache_info.append("❌ Smalltalk cache not available")
    
    cache_info.append("")
    
    # Cache statistics summary
    cache_info.append("### CACHE STATISTICS SUMMARY")
    total_entities = len(CHAMPIONS_LIST) + len(BOSSES_LIST)
    total_mappings = len(RARITY_MAPPING) + len(CLASS_MAPPING) + len(AFFINITY_MAPPING)
    
    cache_info.append(f"📈 Total Cached Entities: {total_entities}")
    cache_info.append(f"📈 Total Mapping Categories: {total_mappings}")
    cache_info.append(f"📈 Total Alias Mappings: {len(ALIAS_TO_NAME_MAPPING)}")
    
    # Memory efficiency info
    if CHAMPIONS_LIST:
        cache_info.append(f"⚡ Cache Status: ACTIVE - Fast lookups enabled")
        cache_info.append(f"⚡ Performance: Static data queries return instantly")
    else:
        cache_info.append(f"⚠️  Cache Status: INACTIVE - Database queries required")
    
    return "\n".join(cache_info)
