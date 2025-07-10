#!/usr/bin/env python3
"""
Workload LLM Tools
Main module that imports and exposes all LLM tools
"""

import logging

# Import new PostgreSQL RAG-based tool functions
from tools.db_rag_get_champion_details import db_rag_get_champion_details
from tools.db_rag_get_boss_details import db_rag_get_boss_details
from tools.db_rag_get_mechanic_details import db_rag_get_mechanic_details
from tools.db_rag_get_gameplay_details import db_rag_get_gameplay_details
from tools.db_rag_get_general_knowledge import db_rag_get_general_knowledge
from tools.db_rag_get_location_details import db_rag_get_location_details
from tools.db_rag_get_battle_details import db_rag_get_battle_details
from tools.db_get_ux_details import db_get_ux_details
from tools.db_get_champions_list import db_get_champions_list
from tools.db_get_screen_context_help import db_get_screen_context_help
from tools.db_rag_get_smalltalk import db_rag_get_smalltalk


# Import PostgreSQL database tool functions
from tools.db_get_champion_details import db_get_champion_details
from tools.db_get_champion_details_byid import db_get_champion_details_byid
from tools.db_get_battle_details import db_get_battle_details
from tools.db_get_battle_details_byid import db_get_battle_details_byid

# Import lore report tool function
from tools.db_get_lore_details import db_get_lore_details

# Import new PostgreSQL functions with trait filtering
from tools.db_find_strongest_champions import db_find_strongest_champions
from tools.db_find_champions_stronger_than import db_find_champions_stronger_than
from tools.db_get_champions_by_traits import db_get_champions_by_traits
from tools.db_compare_champions import db_compare_champions
from tools.db_find_champions import db_find_champions

# Import supporting functions that remain in original modules
from workload_game_cache import (
    get_cache_info,
    set_current_json_data
)

# RAG search functionality moved to PostgreSQL db_rag_* functions

from tools_schemas import get_function_schemas

# Logger
logger = logging.getLogger("Workload LLM Tools")

#######################
# Available Functions Dictionary
#######################

# TODO Functions to move to be 'proactive'
# TODO Functions to merge
# - getChampion()
#   - db_rag_get_champion_details
#   - db_get_champion_details
#   - db_get_champion_details_byid
#   - if fails, should return - No such champion found. Avalible champions are: <db_get_champions_list()>
# - getBossInfo()
#   - db_rag_get_boss_details
#   - if fails to find anything call other function wih information: No Boss Info found, 
#   - and should Call RAG databse for more information
# - searchDatabases()
#   - db_rag_get_general_knowledge
#   - db_rag_get_location_details
#   - db_rag_get_battle_details
#   - db_get_battle_details
#   - db_get_battle_details_byid
# - getBattleDetails()
#   - db_rag_get_battle_details
#   - db_get_battle_details
#   - db_get_battle_details_byid
# - notKnowHowToName()
#   - db_get_screen_context_help()
#   - db_get_ux_details()
# - compareChampions()
# - Rest of the tools as they are. Or left for merge later
# 
# Tools that should be called when proper embedding found in DB 'proactive' tools.
# Search after every querry BEFORE LLM generation.
# - db_rag_get_smalltalk
# - db_rag_get_champion_details (high treshold) 
# - db_rag_get_boss_details (high treshold)
# - db_rag_get_general_knowledge
# - db_rag_get_gameplay_details

# Available LLM tools for function calling
available_llm_functions = {
    'db_get_champions_list': {
        'function': db_get_champions_list,
        'description': 'Get complete list of all available champions'
    },
    'db_rag_get_champion_details': {
        'function': db_rag_get_champion_details,
        'description': 'Get detailed information about a specific champion'
    },
    'db_rag_get_boss_details': {
        'function': db_rag_get_boss_details,
        'description': 'Get detailed information about a specific boss'
    },
    'db_get_ux_details': {
        'function': db_get_ux_details,
        'description': 'Search UX and interface information from database'
    },
    'db_rag_get_mechanic_details': {
        'function': db_rag_get_mechanic_details,
        'description': 'Search game mechanics information from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_rag_get_gameplay_details': {
        'function': db_rag_get_gameplay_details,
        'description': 'Search gameplay strategies and tactics from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_rag_get_general_knowledge': {
        'function': db_rag_get_general_knowledge,
        'description': 'Search entire knowledge base'
    },
    'db_rag_get_location_details': {
        'function': db_rag_get_location_details,
        'description': 'Search location information'
    },
    'db_rag_get_battle_details': {
        'function': db_rag_get_battle_details,
        'description': 'Search battle information'
    },
    'db_get_screen_context_help': {
        'function': db_get_screen_context_help,
        'description': 'Get contextual help for current screen/UI state'
    },
    'db_rag_get_smalltalk': {
        'function': db_rag_get_smalltalk,
        'description': 'Get smalltalk context for casual conversation'
    },
    'db_get_champion_details': {
        'function': db_get_champion_details,
        'description': 'Get detailed champion information including stats, abilities, and battle recommendations'
    },
    'db_get_champion_details_byid': {
        'function': db_get_champion_details_byid,
        'description': 'Get detailed champion information by ID'
    },
    'db_get_lore_details': {
        'function': db_get_lore_details,
        'description': 'Get lore information from database'
    },
    'db_find_strongest_champions': {
        'function': db_find_strongest_champions,
        'description': 'Find the strongest champions based on total power with optional trait filtering (rarity, affinity, class_type)'
    },
    'db_find_champions_stronger_than': {
        'function': db_find_champions_stronger_than,
        'description': 'Find champions stronger than reference champion with optional trait filtering (rarity, affinity, class_type)'
    },
    'db_get_champions_by_traits': {
        'function': db_get_champions_by_traits,
        'description': 'Find champions that match specified traits (rarity, affinity, class_type) with power rankings and AND logic'
    },
    'db_compare_champions': {
        'function': db_compare_champions,
        'description': 'Compare two or more champions side by side with comprehensive analysis of stats, traits, roles, and recommendations'
    },
    'db_find_champions': {
        'function': db_find_champions,
        'description': 'Search for champions by name with basic information (rarity, affinity, class, faction)'
    },
    'db_get_battle_details': {
        'function': db_get_battle_details,
        'description': 'Get detailed battle information including battle summary, participants, objectives, and strategic analysis'
    },
    'db_get_battle_details_byid': {
        'function': db_get_battle_details_byid,
        'description': 'Get detailed battle information by exact battle ID'
    }
}

# Available LLM tools by ID (temporarily disabled - use internal IDs instead of names)
available_llm_functions_by_id = {
}

# Import internal/proactive tools that are not exposed to LLM
from tools.db_get_random_greetings import db_get_random_greetings

# Available proactive/internal tools for system use (not exposed to LLM)
available_proactive_tools = {
    'db_get_random_greetings': {
        'function': db_get_random_greetings,
        'description': 'Get random greeting (internal proactive use only)'
    }
}

# Combined function registry for proactive tool execution
available_all_tools = {**available_llm_functions, **available_proactive_tools}

# Helper functions
def get_function_by_name(name):
    """Get function object by name"""
    return available_llm_functions.get(name, {}).get('function')

# TODO Validate if this is correct way of defining tool for ChatGPT

def get_tools_info() -> str:
    """
    Get detailed information about all available LLM tools
    
    Returns:
        str: Detailed tools information including descriptions and usage
    """
    tools_info = []
    
    tools_info.append("### AVAILABLE LLM TOOLS")
    tools_info.append(f"📊 Total Tools: {len(available_all_tools)}")
    tools_info.append("")
    
    # Generate tool documentation dynamically from available_all_tools
    tools_info.append("### 📋 TOOL REGISTRY")
    tools_info.append("Available tools and their descriptions:")
    tools_info.append("")
    
    for tool_name, tool_info in available_all_tools.items():
        tools_info.append(f"🔸 **{tool_name}**")
        tools_info.append(f"   📝 Description: {tool_info['description']}")
        tools_info.append("")
    
    # Tool Usage Statistics
    tools_info.append("### 📊 TOOL SUMMARY")
    tools_info.append(f"📈 Total Available: {len(available_llm_functions)} LLM tools")
    tools_info.append(f"🔧 Total Internal: {len(available_proactive_tools)} proactive tools")
    tools_info.append(f"🗃️ Total Combined: {len(available_all_tools)} tools")
    tools_info.append("🗃️ All tools use PostgreSQL database for data access")
    tools_info.append("")
    
    
    return "\n".join(tools_info)
