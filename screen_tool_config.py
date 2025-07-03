#!/usr/bin/env python3
"""
Screen-Tool Configuration System
Defines rules for proactive tool calling based on current screen context
"""

import logging
import sqlite3
import os

logger = logging.getLogger("Workload Screen Tools")


def tools_translate(text_by_id: str) -> str:
    """
    Translate text ID to human readable text from translations table
    
    Args:
        text_by_id (str): ID to translate (e.g. "champion.sw1.droideka")
        
    Returns:
        str: Translated text or original ID if not found
    """
    try:
        db_base_path = os.getenv("WORKLOAD_DB_PATH", "/mnt/raid/dev/WorkloadData/DB_V1")
        db_path = os.path.join(db_base_path, "gcs_data.db.sqlite")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Look for direct match first
        cursor.execute("SELECT english_text FROM translations WHERE key_name = ?", (text_by_id,))
        result = cursor.fetchone()
        
        if result:
            conn.close()
            return result[0]
        
        # If no direct match, try with .name suffix
        name_key = f"{text_by_id}.name"
        cursor.execute("SELECT english_text FROM translations WHERE key_name = ?", (name_key,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]
        else:
            logger.warning(f"⚠️ No translation found for: {text_by_id}")
            return text_by_id
            
    except Exception as e:
        logger.error(f"❌ Error translating {text_by_id}: {str(e)}")
        return text_by_id

# Screen-to-tool mapping configuration
SCREEN_TOOL_RULES = {
    "ChampionEquipmentPanelPresenter": {
        "context_tool": {
            "tool": "db_get_ux_details",
            "parameters": {"query": "ChampionFeatureModelsPresenter"}
        },
        "data_tools": [
            {
                "tool": "gcs_get_character_details_by_id",
                "json_field": "ChampionConfigId",
                "parameter_name": "character_id"
            }
        ],
        "prompt_injection": {
            "template": "You are currently on the Champion Details screen. The user is viewing champion '{ChampionConfigId_translated}'. If user doesn't ask specific question focus your responses on this specific champion and the champion management interface they are currently using.",
            "required_fields": ["ChampionConfigId"],
            "translate_fields": {"ChampionConfigId_translated": "ChampionConfigId"}
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
    translate_fields = prompt_config.get("translate_fields", {})
    
    # Check if all required fields are available
    missing_fields = [field for field in required_fields if field not in data_fields]
    if missing_fields:
        logger.warning(f"⚠️ Missing required fields for prompt injection: {missing_fields}")
        return ""
    
    # Build substitution dictionary
    substitutions = {"screen_name": screen_name}
    substitutions.update(data_fields)
    
    # Add translated fields
    for translated_key, source_key in translate_fields.items():
        if source_key in data_fields:
            translated_value = tools_translate(data_fields[source_key])
            substitutions[translated_key] = translated_value
            logger.info(f"🔄 Translated {source_key}='{data_fields[source_key]}' → {translated_key}='{translated_value}'")
    
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