#!/usr/bin/env python3
"""
Screen-Tool Configuration System
Defines rules for proactive tool calling based on current screen context
"""

import logging
import os
from db_postgres import execute_query

logger = logging.getLogger("Workload Screen Tools")


def get_champion_name_by_id(champion_id: str) -> str:
    """
    Get champion name from PostgreSQL champions table by champion_id
    
    Args:
        champion_id (str): Champion ID to lookup (e.g. "champion.sw1.droideka")
        
    Returns:
        str: Champion name or original ID if not found
    """
    try:
        # Query PostgreSQL for champion name
        results = execute_query("""
            SELECT champion_name 
            FROM champion_details 
            WHERE champion_id = %s
        """, (champion_id,))
        
        if results and len(results) > 0:
            champion_name = results[0]["champion_name"]
            logger.info(f"✅ Found champion name for {champion_id}: {champion_name}")
            return champion_name
        else:
            logger.warning(f"⚠️ No champion found for ID: {champion_id}")
            return champion_id
            
    except Exception as e:
        logger.error(f"❌ Error getting champion name for {champion_id}: {str(e)}")
        return champion_id


def get_battle_name_by_id(battle_id: str) -> str:
    """
    Get battle name from PostgreSQL battles table by battle_id
    
    Args:
        battle_id (str): Battle ID to lookup (e.g. "d1_m1_b1")
        
    Returns:
        str: Battle name or original ID if not found
    """
    try:
        # Query PostgreSQL for champion name
        results = execute_query("""
            SELECT battle_name 
            FROM battle_details 
            WHERE battle_id = %s
        """, (battle_id,))
        
        if results and len(results) > 0:
            battle_name = results[0]["battle_name"]
            logger.info(f"✅ Found battle name for {battle_id}: {battle_name}")
            return battle_name
        else:
            logger.warning(f"⚠️ No battle found for ID: {battle_id}")
            return battle_id
            
    except Exception as e:
        logger.error(f"❌ Error getting battle name for {battle_id}: {str(e)}")
        return battle_id
    
# Screen-to-tool mapping configuration
SCREEN_TOOL_RULES = {
    "ChampionEquipmentPanelPresenter": {
        "context_tool": {
            "tool": "db_get_ux_details",
            "parameters": {"query": "ChampionEquipmentPanelPresenter"}
        },
        "data_tools": [
            {
                "tool": "db_get_champion_details_byid",
                "json_field": "ChampionConfigId",
                "parameter_name": "champion_id"
            }
        ],
        "prompt_injection": {
            "template": "You are currently on the Champion Details screen. The user is viewing champion '{champion_name}'. If user doesn't ask specific question focus your responses on this specific champion and the champion management interface they are currently using.",
            "required_fields": ["ChampionConfigId"],
            "lookup_fields": {"champion_name": "ChampionConfigId"}
        }
    },
    "CampaignTeamSelectUIPresenter": {
        "context_tool": {
            "tool": "db_get_ux_details",
            "parameters": {"query": "CampaignTeamSelectUIPresenter"}
        },
        "data_tools": [
            {
                "tool": "db_get_battle_details_byid",
                "json_field": "BattleId",
                "parameter_name": "battle_id"
            }
        ],
        "prompt_injection": {
            "template": "You are currently on the Campaign Team Select screen just before the battle'{battle_name}'. User goal is to select best team that can defeat opponents. Assist him to select best team and choose best strategy.",            
            "required_fields": ["BattleId"],
            "lookup_fields": {"battle_name": "BattleId"}
        }
    },
    # Add more screen configurations here
    "MainMenuScreen": {
        "context_tool": {
            "tool": "db_get_ux_details", 
            "parameters": {"query": "MainMenuScreen"}
        },
        "data_tools": [],
        "prompt_injection": {
            "template": "You are currently on the Main Menu screen. The user is in the main navigation area of the game. If user doesn't ask specific question focus on helping them navigate or understand available options.",
            "required_fields": []
        }
    }
}

# Fallback rules for screens not explicitly configured
DEFAULT_SCREEN_RULES = {
    "context_tool": {
        "tool": "db_get_ux_details",
        "parameters": {"query": "{screen_name}"}  # Will be replaced with actual screen name
    },
    "data_tools": [],
    "prompt_injection": {
        "template": "You are currently on the '{screen_name}' screen. The user is viewing this interface. If user doesn't ask specific question focus your responses on helping them with this specific screen and its functionality.",
        "required_fields": []
    }
}


def get_screen_tool_rules(screen_name: str) -> dict:
    """
    Get tool rules for a specific screen
    
    Args:
        screen_name (str): Name of the current screen
        
    Returns:
        dict: Tool rules configuration for the screen
    """
    if screen_name in SCREEN_TOOL_RULES:
        logger.info(f"✅ Found specific rules for screen: {screen_name}")
        return SCREEN_TOOL_RULES[screen_name]
    
    # Use default rules with screen name substitution
    logger.info(f"⚠️ Using default rules for screen: {screen_name}")
    default_rules = DEFAULT_SCREEN_RULES.copy()
    
    # Replace placeholder with actual screen name
    if "context_tool" in default_rules:
        context_tool = default_rules["context_tool"].copy()
        if "parameters" in context_tool and "query" in context_tool["parameters"]:
            context_tool["parameters"]["query"] = context_tool["parameters"]["query"].replace("{screen_name}", screen_name)
        default_rules["context_tool"] = context_tool
    
    return default_rules


def get_all_configured_screens() -> list:
    """
    Get list of all explicitly configured screen names
    
    Returns:
        list: List of configured screen names
    """
    return list(SCREEN_TOOL_RULES.keys())


def is_screen_configured(screen_name: str) -> bool:
    """
    Check if a screen has explicit configuration
    
    Args:
        screen_name (str): Name of the screen to check
        
    Returns:
        bool: True if screen has explicit rules, False otherwise
    """
    return screen_name in SCREEN_TOOL_RULES


def build_prompt_injection(screen_name: str, data_fields: dict) -> str:
    """
    Build prompt injection text for a specific screen context
    
    Args:
        screen_name (str): Name of the current screen
        data_fields (dict): Available data fields from JSON
        
    Returns:
        str: Formatted prompt injection text or empty string if not applicable
    """
    rules = get_screen_tool_rules(screen_name)
    prompt_config = rules.get("prompt_injection")
    
    if not prompt_config:
        logger.warning(f"⚠️ No prompt injection configured for screen: {screen_name}")
        return ""
    
    template = prompt_config.get("template", "")
    required_fields = prompt_config.get("required_fields", [])
    lookup_fields = prompt_config.get("lookup_fields", {})
    
    # Check if all required fields are available
    missing_fields = [field for field in required_fields if field not in data_fields]
    if missing_fields:
        logger.warning(f"⚠️ Missing required fields for prompt injection: {missing_fields}")
        return ""
    
    # Build substitution dictionary
    substitutions = {"screen_name": screen_name}
    substitutions.update(data_fields)
    
    # Add lookup fields (champion name from PostgreSQL)
    for lookup_key, source_key in lookup_fields.items():
        if source_key in data_fields:
            if lookup_key == "champion_name":
                champion_name = get_champion_name_by_id(data_fields[source_key])
                substitutions[lookup_key] = champion_name
                logger.info(f"🔄 Looked up {source_key}='{data_fields[source_key]}' → {lookup_key}='{champion_name}'")
            elif lookup_key == "battle_name":
                battle_name = get_battle_name_by_id(data_fields[source_key])
                substitutions[lookup_key] = battle_name
                logger.info(f"🔄 Looked up {source_key}='{data_fields[source_key]}' → {lookup_key}='{battle_name}'")
    
    try:
        # Perform template substitution
        prompt_injection = template.format(**substitutions)
        logger.info(f"✅ Built prompt injection for {screen_name}: {len(prompt_injection)} chars")
        return prompt_injection
        
    except KeyError as e:
        logger.error(f"❌ Template substitution failed for {screen_name}: missing key {e}")
        return ""
    except Exception as e:
        logger.error(f"❌ Error building prompt injection for {screen_name}: {str(e)}")
        return ""