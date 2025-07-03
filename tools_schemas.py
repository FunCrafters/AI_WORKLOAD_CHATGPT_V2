#!/usr/bin/env python3
"""
Workload Function Schemas
Function schemas for LLM tool calling
"""

def get_function_schemas():
    """
    Returns complete function schemas for all available tools
    """
    return [
        # Static data tools (no parameters)
        {
            "type": "function",
            "function": {
                "name": "cache_get_champions_list",
                "description": "Get complete list of all available champions in the game",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "cache_get_bosses_list", 
                "description": "Get complete list of all available bosses in the game",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        
        # RAG-based detail tools
        {
            "type": "function",
            "function": {
                "name": "rag_get_champion_details",
                "description": "Get detailed information about a specific champion including core and gameplay information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "champion_name": {
                            "type": "string",
                            "description": "Exact name of the champion to get details for"
                        }
                    },
                    "required": ["champion_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "rag_get_boss_details",
                "description": "Get detailed information about a specific boss including core and gameplay information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "boss_name": {
                            "type": "string",
                            "description": "Exact name of the boss to get details for"
                        }
                    },
                    "required": ["boss_name"]
                }
            }
        },
        
        # Category-based RAG search tools
        {
            "type": "function",
            "function": {
                "name": "db_get_ux_details",
                "description": "Search for UX (User Experience) related information and interface details",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for UX information (e.g., 'interface', 'menu', 'navigation')"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "rag_get_mechanics_details",
                "description": "Search for game mechanics information including rules, systems, and gameplay mechanics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for mechanics information (e.g., 'combat', 'abilities', 'stats')"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "rag_get_gameplay_details",
                "description": "Search for gameplay information including strategies, tactics, and game flow",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for gameplay information (e.g., 'strategy', 'tactics', 'progression')"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        
        # General knowledge base - REMOVED search_type parameter
        {
            "type": "function",
            "function": {
                "name": "rag_get_general_knowledge",
                "description": "Search general knowledge base - searches both general documents and Q&A sections",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for knowledge base"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        
        # Smalltalk context tool
        {
            "type": "function",
            "function": {
                "name": "rag_get_smalltalk_context",
                "description": "Search for something funny or interesting.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for something funny or interesting"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        
        # Screen context help tool
        {
            "type": "function",
            "function": {
                "name": "db_get_screen_context_help",
                "description": "Get contextual help for current screen/UI state. Available only when screenData is present in JSON. Uses simplified screen detection and database lookup.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_question": {
                            "type": "string",
                            "description": "User's question about the current screen/interface (e.g., 'where am I?', 'what can I do here?', 'how to use this?', 'what is this screen for?')"
                        }
                    },
                    "required": ["user_question"]
                }
            }
        },
        
        
        # GCS Database tools
        {
            "type": "function",
            "function": {
                "name": "gcs_get_champion_details",
                "description": "Get detailed champion information including complete stats, abilities with effects, traits, power ranking, and battle recommendations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "champion_name": {
                            "type": "string",
                            "description": "Champion name or partial name to search for (e.g., 'Han Solo', 'Luke', 'Vader')"
                        }
                    },
                    "required": ["champion_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_get_champion_abilities",
                "description": "Get abilities information for a champion by name. Returns human-readable ability descriptions with clean formatting.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "champion_name": {
                            "type": "string",
                            "description": "Champion name or partial name to search for abilities (e.g., 'Han Solo', 'Luke', 'Vader')"
                        }
                    },
                    "required": ["champion_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_find_characters",
                "description": "Search for characters (both champions and enemies) by name. Returns comprehensive results with battle information for enemies and basic information for champions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Character name or partial name to search for. Searches both champions and enemies (e.g., 'Luke', 'Stormtrooper', 'Imperial')"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_find_champions",
                "description": "Search for champions only by name. Returns only champions, no enemies. Use when you specifically need champion information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Champion name or partial name to search for (e.g., 'Luke', 'Han Solo', 'Vader')"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_find_enemies",
                "description": "Search for enemies only by name with battle appearance information. Returns only enemies, no champions. Use when you specifically need enemy information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Enemy name or partial name to search for (e.g., 'Stormtrooper', 'Imperial', 'Droid')"
                        }
                    },
                    "required": ["name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_find_strongest_champions",
                "description": "Find the strongest champions based on total power (attack + defense + health). Provides statistical analysis and distribution by traits.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of top champions to return (default: 10, max: 50)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_find_strongest_enemies",
                "description": "Find the strongest enemies based on total power (attack + defense + health). Includes battle appearance counts and faction distribution.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of top enemies to return (default: 10, max: 50)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_find_champions_stronger_than",
                "description": "Find champions who are stronger than a specified reference champion. Compares total power (attack + defense + health) and shows power differences.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "character_name": {
                            "type": "string",
                            "description": "Name of the reference champion to compare against (e.g., 'Han Solo', 'Luke', 'Vader')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of stronger champions to return (default: 20, max: 50)",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["character_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_compare_characters",
                "description": "Compare two or more characters side by side with comprehensive analysis of stats, abilities, roles, and intelligent recommendations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "character_names": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of character names to compare (minimum 2 required, e.g., ['Han Solo', 'Luke Skywalker'])",
                            "minItems": 2,
                            "maxItems": 5
                        },
                        "detailed": {
                            "type": "boolean",
                            "description": "Whether to include detailed analysis (default: true)",
                            "default": True
                        }
                    },
                    "required": ["character_names"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_get_champions_by_traits",
                "description": "Find champions that match specified traits (rarity, affinity, class). Uses AND logic - all traits must match. Available traits: legendary/epic/rare/uncommon/common, red/blue/green/yellow/purple, attacker/defender/support.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "traits": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of trait values to filter by (e.g., ['legendary', 'red'], ['epic', 'support']). Available: rarity (legendary/epic/rare/uncommon/common), affinity (red/blue/green/yellow/purple), class (attacker/defender/support)",
                            "minItems": 1,
                            "maxItems": 3
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of champions to return (default: 50, max: 100)",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 100
                        }
                    },
                    "required": ["traits"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "db_get_lore_details",
                "description": "Get specialized report.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "champion_name": {
                            "type": "string",
                            "description": "Name of the champion"
                        }
                    },
                    "required": ["champion_name"]
                }
            }
        }
    ]

def get_function_schemas_by_id():
    """
    Returns function schemas for tools that use internal IDs (temporarily disabled)
    These tools require internal database IDs instead of character names
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "gcs_get_character_details_by_id",
                "description": "Get comprehensive details for any character (champion or enemy) using their internal database ID. Use when you have a specific character ID from previous searches.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "character_id": {
                            "type": "string",
                            "description": "Internal character ID from the database (e.g., 'hansolo_classic', 'luke_jedi', 'vader_empire')"
                        }
                    },
                    "required": ["character_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "gcs_get_character_abilities_by_id",
                "description": "Get abilities information for any character (champion or enemy) by their internal database ID. Returns human-readable ability descriptions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "character_id": {
                            "type": "string",
                            "description": "Internal character ID from the database (e.g., 'champion.sw5.luke', 'enemy.imperial.stormtrooper')"
                        }
                    },
                    "required": ["character_id"]
                }
            }
        }
    ]
