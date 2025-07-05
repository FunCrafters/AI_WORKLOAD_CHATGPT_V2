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
from tools.db_rag_get_battles import db_rag_get_battles
from tools.db_get_ux_details import db_get_ux_details
from tools.db_get_champions_list import db_get_champions_list
from tools.db_get_screen_context_help import db_get_screen_context_help
from tools.db_rag_get_smalltalk import db_rag_get_smalltalk


# Import GCS database tool functions
from tools.db_get_champion_details import db_get_champion_details, db_get_champion_details_byid

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
    set_current_json_data,
    get_random_smalltalk_topic_and_knowledge
)

from workload_rag_search import rag_search

from tools_schemas import get_function_schemas

# Logger
logger = logging.getLogger("Workload LLM Tools")

#######################
# Available Functions Dictionary
#######################

# Available LLM tools for function calling with metadata
available_llm_functions = {
    'db_get_champions_list': {
        'function': db_get_champions_list,
        'is_rag': False,
        'is_gcs': False,
        'category': 'static',
        'description': 'Get complete list of all available champions'
    },
    'db_rag_get_champion_details': {
        'function': db_rag_get_champion_details,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Get detailed information about a specific champion from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_rag_get_boss_details': {
        'function': db_rag_get_boss_details,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Get detailed information about a specific boss from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_get_ux_details': {
        'function': db_get_ux_details,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Search UX and interface information from database'
    },
    'db_rag_get_mechanic_details': {
        'function': db_rag_get_mechanic_details,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Search game mechanics information from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_rag_get_gameplay_details': {
        'function': db_rag_get_gameplay_details,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Search gameplay strategies and tactics from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_rag_get_general_knowledge': {
        'function': db_rag_get_general_knowledge,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Search entire knowledge base from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_rag_get_location_details': {
        'function': db_rag_get_location_details,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Search location information from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_rag_get_battles': {
        'function': db_rag_get_battles,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Search battle information from PostgreSQL rag_vectors using Ollama embeddings'
    },
    'db_get_screen_context_help': {
        'function': db_get_screen_context_help,
        'is_rag': False,
        'is_gcs': False,
        'category': 'context',
        'description': 'Get contextual help for current screen/UI state'
    },
    'db_rag_get_smalltalk': {
        'function': db_rag_get_smalltalk,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Get smalltalk context for casual conversation using PostgreSQL embedding similarity'
    },
    'db_get_champion_details': {
        'function': db_get_champion_details,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Get detailed champion information from PostgreSQL database including stats, abilities, and battle recommendations'
    },
    'db_get_champion_details_byid': {
        'function': db_get_champion_details_byid,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Get detailed champion information by ID from PostgreSQL database'
    },
    'db_get_lore_details': {
        'function': db_get_lore_details,
        'is_rag': False,
        'is_gcs': False,
        'category': 'lore',
        'description': 'Get lore information from database'
    },
    'db_find_strongest_champions': {
        'function': db_find_strongest_champions,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Find the strongest champions based on total power with optional trait filtering (rarity, affinity, class_type) using PostgreSQL'
    },
    'db_find_champions_stronger_than': {
        'function': db_find_champions_stronger_than,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Find champions stronger than reference champion with optional trait filtering (rarity, affinity, class_type) using PostgreSQL'
    },
    'db_get_champions_by_traits': {
        'function': db_get_champions_by_traits,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Find champions that match specified traits (rarity, affinity, class_type) with power rankings using PostgreSQL and AND logic'
    },
    'db_compare_champions': {
        'function': db_compare_champions,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Compare two or more champions side by side with comprehensive analysis of stats, traits, roles, and recommendations using PostgreSQL'
    },
    'db_find_champions': {
        'function': db_find_champions,
        'is_rag': False,
        'is_gcs': False,
        'category': 'database',
        'description': 'Search for champions by name with basic information (rarity, affinity, class, faction) using PostgreSQL'
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
        'is_rag': False,
        'is_gcs': False,
        'category': 'social_internal',
        'description': 'Get random greeting (internal proactive use only)'
    }
}

# Combined function registry for proactive tool execution
available_all_tools = {**available_llm_functions, **available_proactive_tools}

# Helper functions to get function categories
def get_rag_functions():
    """Get list of RAG function names"""
    return [name for name, meta in available_llm_functions.items() if meta['is_rag']]

def get_gcs_functions():
    """Get list of GCS function names (deprecated - no GCS functions remain)"""
    return []

def get_static_functions():
    """Get list of static function names"""
    return [name for name, meta in available_llm_functions.items() if not meta['is_rag'] and not meta['is_gcs']]

def get_function_by_name(name):
    """Get function object by name"""
    return available_llm_functions.get(name, {}).get('function')

def is_rag_function(name):
    """Check if function is a RAG function"""
    return available_llm_functions.get(name, {}).get('is_rag', False)

def is_gcs_function(name):
    """Check if function is a GCS function (deprecated - no GCS functions remain)"""
    return False

def get_tools_info() -> str:
    """
    Get detailed information about all available LLM tools
    
    Returns:
        str: Detailed tools information including descriptions and usage
    """
    tools_info = []
    
    tools_info.append("### AVAILABLE LLM TOOLS")
    tools_info.append(f"📊 Total Tools: {len(available_llm_functions)}")
    tools_info.append("")
    
    # Static Data Tools (Cache-based)
    tools_info.append("### 🗂️ STATIC DATA TOOLS (Cache-based)")
    tools_info.append("These tools use cached data for instant responses:")
    tools_info.append("")
    
    tools_info.append("🔸 **db_get_champions_list**")
    tools_info.append("   📝 Description: Get complete list of all available champions")
    tools_info.append("   ❓ Answers: 'List all champions', 'What champions are available?'")
    tools_info.append("   ⚡ Data Source: PostgreSQL database")
    tools_info.append("")
    
    
    # PostgreSQL RAG-based Detail Tools
    tools_info.append("### 🔍 POSTGRESQL RAG-BASED DETAIL TOOLS (Knowledge Base)")
    tools_info.append("These tools search the PostgreSQL rag_vectors knowledge base using Ollama embeddings:")
    tools_info.append("")
    
    tools_info.append("🔸 **db_rag_get_champion_details**")
    tools_info.append("   📝 Description: Get detailed information about a specific champion")
    tools_info.append("   ❓ Answers: 'Tell me about Han Solo', 'Champion details for Luke'")
    tools_info.append("   📋 Parameters: champion_name (exact name)")
    tools_info.append("   🗄️ Data Source: PostgreSQL rag_vectors (chunk_section=CHAMPIONS)")
    tools_info.append("   📚 Includes: Core info, gameplay info, abilities, stats")
    tools_info.append("")
    
    tools_info.append("🔸 **db_rag_get_boss_details**")
    tools_info.append("   📝 Description: Get detailed information about a specific boss")
    tools_info.append("   ❓ Answers: 'Tell me about Darth Vader boss', 'Boss mechanics'")
    tools_info.append("   📋 Parameters: boss_name (exact name)")
    tools_info.append("   🗄️ Data Source: PostgreSQL rag_vectors (chunk_section=BOSSES)")
    tools_info.append("   📚 Includes: Core info, gameplay info, strategies")
    tools_info.append("")
    
    # Category-based PostgreSQL RAG Tools
    tools_info.append("### 📂 CATEGORY-BASED POSTGRESQL RAG TOOLS (Knowledge Base)")
    tools_info.append("These tools search specific categories in the PostgreSQL rag_vectors knowledge base:")
    tools_info.append("")
    
    tools_info.append("🔸 **db_get_ux_details**")
    tools_info.append("   📝 Description: Search UX and interface information")
    tools_info.append("   ❓ Answers: 'How does the interface work?', 'Menu navigation'")
    tools_info.append("   📋 Parameters: query (search terms)")
    tools_info.append("   🗄️ Data Source: Database search (ux.db.sqlite)")
    tools_info.append("   📚 Includes: Interface, menus, navigation, user experience")
    tools_info.append("")
    
    tools_info.append("🔸 **db_rag_get_mechanic_details**")
    tools_info.append("   📝 Description: Search game mechanics information")
    tools_info.append("   ❓ Answers: 'How does combat work?', 'Ability mechanics'")
    tools_info.append("   📋 Parameters: query (search terms)")
    tools_info.append("   🗄️ Data Source: PostgreSQL rag_vectors (chunk_section=MECHANICS)")
    tools_info.append("   📚 Includes: Rules, systems, combat, abilities")
    tools_info.append("")
    
    tools_info.append("🔸 **db_rag_get_gameplay_details**")
    tools_info.append("   📝 Description: Search gameplay strategies and tactics")
    tools_info.append("   ❓ Answers: 'Best strategies?', 'How to progress?'")
    tools_info.append("   📋 Parameters: query (search terms)")
    tools_info.append("   🗄️ Data Source: PostgreSQL rag_vectors (chunk_section=GAMEPLAY)")
    tools_info.append("   📚 Includes: Strategies, tactics, progression, tips")
    tools_info.append("")
    
    tools_info.append("🔸 **db_rag_get_locations**")
    tools_info.append("   📝 Description: Search location information")
    tools_info.append("   ❓ Answers: 'Tell me about Tatooine', 'Planet descriptions'")
    tools_info.append("   📋 Parameters: query (search terms)")
    tools_info.append("   🗄️ Data Source: PostgreSQL rag_vectors (chunk_section=LOCATIONS)")
    tools_info.append("   📚 Includes: Planets, places, environments, descriptions")
    tools_info.append("")
    
    tools_info.append("🔸 **db_rag_get_battles**")
    tools_info.append("   📝 Description: Search battle information")
    tools_info.append("   ❓ Answers: 'Tell me about famous battles', 'War strategies'")
    tools_info.append("   📋 Parameters: query (search terms)")
    tools_info.append("   🗄️ Data Source: PostgreSQL rag_vectors (chunk_section=BATTLES)")
    tools_info.append("   📚 Includes: Battles, wars, conflicts, military history")
    tools_info.append("")
    
    # General Knowledge Tool
    tools_info.append("### 🌐 GENERAL KNOWLEDGE TOOL (Knowledge Base)")
    tools_info.append("Universal search tool for any information:")
    tools_info.append("")
    
    tools_info.append("🔸 **db_rag_get_general_knowledge**")
    tools_info.append("   📝 Description: Search entire knowledge base - both general documents and Q&A")
    tools_info.append("   ❓ Answers: Any question about the game or characters")
    tools_info.append("   📋 Parameters: query (search terms)")
    tools_info.append("   🗄️ Data Source: PostgreSQL rag_vectors (all chunk_sections)")
    tools_info.append("   📚 Includes: All categories, documents, Q&A sections")
    tools_info.append("")
    
    # Smalltalk Context Tool
    tools_info.append("### 💬 SMALLTALK CONTEXT TOOL (Conditional)")
    tools_info.append("Casual conversation tool available only in smalltalk mode:")
    tools_info.append("")
    
    tools_info.append("🔸 **db_rag_get_smalltalk**")
    tools_info.append("   📝 Description: Search smalltalk knowledge base for casual conversation topics using PostgreSQL")
    tools_info.append("   ❓ Answers: 'Tell me about Tatooine weather', 'What's life like in cantinas?'")
    tools_info.append("   📋 Parameters: query (search terms for casual topics, optional)")
    tools_info.append("   🗄️ Data Source: PostgreSQL embedding similarity search with Ollama (threshold 0.4)")
    tools_info.append("   📚 Includes: Daily life, culture, entertainment, planets, creatures, social life")
    tools_info.append("   🎯 Variety: Random selection from top 10 similar results for conversation diversity")
    tools_info.append("")
    
    # Screen Context Tool
    tools_info.append("### 🖥️ SCREEN CONTEXT TOOL (Conditional)")
    tools_info.append("Context-aware tool available only when screenData is present:")
    tools_info.append("")
    
    tools_info.append("🔸 **db_get_screen_context_help**")
    tools_info.append("   📝 Description: Get contextual help for current screen/UI state")
    tools_info.append("   ❓ Provides: Simplified screen help based on current screen")
    tools_info.append("   📋 Parameters: user_question (question about current screen)")
    tools_info.append("   🗄️ Data Source: Database search (ux.db.sqlite) + screen detection")
    tools_info.append("   📚 Simple: Direct screen lookup with fallback to combined query")
    tools_info.append("   ⚠️ Availability: Only when JSON contains screenData section")
    tools_info.append("")
    
    # PostgreSQL Database Tools
    tools_info.append("### 🗃️ POSTGRESQL DATABASE TOOLS (Direct Database Access)")
    tools_info.append("These tools provide direct access to the PostgreSQL game database:")
    tools_info.append("")
    
    tools_info.append("🔸 **db_get_champion_details**")
    tools_info.append("   📝 Description: Get comprehensive champion information from PostgreSQL database")
    tools_info.append("   ❓ Answers: 'Tell me about Luke Skywalker stats', 'Champion abilities details'")
    tools_info.append("   📋 Parameters: champion_name (exact or partial name)")
    tools_info.append("")
    
    tools_info.append("🔸 **db_find_champions**")
    tools_info.append("   📝 Description: Search for champions by name with basic information")
    tools_info.append("   ❓ Answers: 'Find Luke champions', 'Search champions with Solo in name'")
    tools_info.append("   📋 Parameters: name (champion name or partial name), limit")
    tools_info.append("")
    
    tools_info.append("🔸 **db_find_strongest_champions**")
    tools_info.append("   📝 Description: Find strongest champions with optional trait filtering")
    tools_info.append("   ❓ Answers: 'Show strongest legendary attackers', 'Top 10 red champions'")
    tools_info.append("   📋 Parameters: limit, rarity, affinity, class_type")
    tools_info.append("")
    
    tools_info.append("🔸 **db_compare_champions**")
    tools_info.append("   📝 Description: Compare champions side by side with comprehensive analysis")
    tools_info.append("   ❓ Answers: 'Compare Han Solo and Luke', 'Vader vs Luke analysis'")
    tools_info.append("   📋 Parameters: champion_names (list of 2-5 names)")
    tools_info.append("")
    
    
    # Tool Usage Statistics
    tools_info.append("### 📊 TOOL CATEGORIES SUMMARY")
    static_tools = get_static_functions()
    rag_tools = get_rag_functions()
    gcs_tools = get_gcs_functions()
    context_tools = [name for name, meta in available_llm_functions.items() if meta['category'] == 'rag_context']
    smalltalk_tools = [name for name, meta in available_llm_functions.items() if meta['category'] == 'rag_smalltalk']
    
    tools_info.append(f"⚡ Static Data Tools: {len(static_tools)} (instant cache-based)")
    tools_info.append(f"🗄️ RAG-based Tools: {len(rag_tools)} (knowledge base search)")
    tools_info.append(f"🗃️ PostgreSQL Database Tools: {len([name for name, meta in available_llm_functions.items() if meta['category'] == 'database'])} (direct database access)")
    tools_info.append(f"🖥️ Context Tools: {len(context_tools)} (conditional availability)")
    tools_info.append(f"💬 Smalltalk Tools: {len(smalltalk_tools)} (smalltalk mode only)")
    tools_info.append(f"📈 Total Available: {len(available_llm_functions)} tools")
    tools_info.append("")
    
    # Performance Information
    tools_info.append("### ⚡ PERFORMANCE CHARACTERISTICS")
    tools_info.append("🚀 **Static Tools**: Sub-millisecond response (memory cache)")
    tools_info.append("🔍 **RAG Tools**: ~100-500ms response (vectorstore search)")
    tools_info.append("🗃️ **PostgreSQL Tools**: ~50-200ms response (direct database queries)")
    tools_info.append("📚 **Knowledge Base**: 7 similarity + 7 Q&A chunks per search")
    tools_info.append("🎯 **Precision**: Exact name matching + semantic similarity")
    tools_info.append("")
    
    # Usage Guidelines
    tools_info.append("### 📋 USAGE GUIDELINES")
    tools_info.append("1. **Lists & Filtering**: Use static tools (db_get_champions_list) for basic lists")
    tools_info.append("2. **Trait Filtering**: Use PostgreSQL tools (db_get_champions_by_traits) for filtering by rarity, affinity, class")
    tools_info.append("3. **Detailed Champion Info**: Use database tools (db_get_champion_details, db_get_champion_details_byid) for comprehensive data")
    tools_info.append("4. **Character Search**: Use PostgreSQL tools (db_find_champions) for champion search")
    tools_info.append("5. **Power Analysis**: Use PostgreSQL tools (db_find_strongest_champions, db_find_champions_stronger_than, db_compare_champions)")
    tools_info.append("6. **RAG Detailed Info**: Use PostgreSQL RAG tools (db_rag_get_champion_details, db_rag_get_boss_details)")
    tools_info.append("7. **Category Search**: Use PostgreSQL category tools (db_rag_get_mechanic_details, db_rag_get_gameplay_details, db_rag_get_locations, db_rag_get_battles)")
    tools_info.append("8. **General Questions**: Use db_rag_get_general_knowledge")
    tools_info.append("9. **Unknown Queries**: Model automatically selects best tool")
    
    return "\n".join(tools_info)
