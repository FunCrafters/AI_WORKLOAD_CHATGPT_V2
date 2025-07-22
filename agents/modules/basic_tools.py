from typing import List

from agents.modules.module import T3RNModule
from session import Session
from tools.db_get_battle_details import db_get_battle_details
from tools.db_get_lore_details import db_get_lore_details
from tools.db_rag_get_battle_details import db_rag_get_battle_details
from tools.db_rag_get_gameplay_details import db_rag_get_gameplay_details
from tools.db_rag_get_general_knowledge import db_rag_get_general_knowledge
from tools.db_rag_get_location_details import db_rag_get_location_details
from tools.db_rag_get_mechanic_details import db_rag_get_mechanic_details
from tools.db_rag_get_smalltalk import db_rag_get_smalltalk
from tools_functions import T3RNTool


class BasicTools(T3RNModule):
    def define_tools(self, session: "Session") -> List["T3RNTool"]:
        return [
            T3RNTool(
                name="getRagSmalltalk",
                function=db_rag_get_smalltalk,
                description="Search smalltalk knowledge base for casual conversation topics",
                system_prompt="""
Tool getRagSmalltalk allows the droid to retrive information about revlevant topics the user might bring up.
You can use this tool to get smalltalks and casual conversation content for example when user asks for:
* Information about an lore, characters, places or events that
You should not use this tool when
* User asks about gameplay mechanics, rules or strategies
* User asks about specific game content that is not related to smalltalk or casual conversation.
Examples:
* "What is tatooine?" use getRagSmalltalk("Tatooine")
* "Do you know something interesting about Jedi robes" use getRagSmalltalk("something interesting about Jedi robes")
* "What's fun to do at Mos Eisley" use getRagSmalltalk("Mos Eisley fun activities")
* "Are you a drioid? What it even means" use getRagSmalltalk("drioid meaning, lore")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for smalltalk topics and casual conversation content in form of a question or keyword.",
                        }
                    },
                    "required": [],
                },
            ),
            T3RNTool(
                name="getMechanicDetails",
                function=db_rag_get_mechanic_details,
                description="Search game mechanics information from PostgreSQL rag_vectors using Ollama embeddings",
                system_prompt="""
Tool getMechanicDetails allows the droid to retrieve detailed information about game mechanics.
You can use this tool when user asks about:
* How specific game systems work
* Rules for combat, abilities, or stats
* Details about game mechanics like crafting, progression, or upgrades
* Questions about how different game elements interact with each other
You should not use this tool when:
* User asks about story or lore elements
* User asks about interface navigation (use getUXDetails instead)
* User is engaging in casual conversation
Examples:
* "How does combat work?" use getMechanicDetails("combat mechanics")
* "What is the relation between colors?" use getMechanicDetails("color relations")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for mechanics information (e.g., 'combat', 'abilities', 'stats')",
                        }
                    },
                    "required": ["query"],
                },
            ),
            T3RNTool(
                name="getGameplayDetails",
                function=db_rag_get_gameplay_details,
                description="Search gameplay strategies and tactics from PostgreSQL rag_vectors using Ollama embeddings",
                system_prompt="""
Tool getGameplayDetails allows the droid to retrieve information about gameplay strategies and tactics.
You can use this tool when user asks about:
* How to approach specific battles or challenges
* Strategies for using particular champions or abilities
* Tactics for progression in the game
* Tips for improving gameplay performance
* General gameplay advice and recommendations
You should not use this tool when:
* User asks about basic mechanics (use getMechanicDetails instead)
* User asks about story elements or lore
* User is asking about interface navigation
Examples:
* "What is the best strategy for using Luke Skywalker?" use getGameplayDetails("Luke Skywalker strategy")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for gameplay information (e.g., 'strategy', 'tactics', 'progression')",
                        }
                    },
                    "required": ["query"],
                },
            ),
            T3RNTool(
                name="getGeneralKnowledge",
                function=db_rag_get_general_knowledge,
                description="Search entire knowledge base",
                system_prompt="""
Tool getGeneralKnowledge allows the droid to search the entire knowledge base for information.
You can use this tool when:
* User asks a question that doesn't clearly fit into other specific categories
* You need broad information that might span multiple domains
* Previous more specific tool searches didn't yield helpful results
* You need to provide comprehensive information on a topic
This is a broad search tool that searches both general documents and Q&A sections across all chunk_sections.
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for knowledge base",
                        }
                    },
                    "required": ["query"],
                },
            ),
            T3RNTool(
                name="getLocationDetails",
                function=db_rag_get_location_details,
                description="Search location information",
                system_prompt="""
Tool getLocationDetails allows the droid to retrieve information about locations in the game.
You can use this tool when user asks about:
* Details about specific planets or environments
* Information about game areas, maps, or regions
* Questions about the geography or features of locations
* Historical significance of locations in the game world
You should not use this tool when:
* User asks about gameplay mechanics not related to locations
* User asks about champions or characters (use champion-specific tools instead)
* User is engaged in casual conversation
Examples:
* "Tell me about Tatooine" use getLocationDetails("Tatooine")
* "What are the environments in the game?" use getLocationDetails("environments")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for location information (e.g., 'Tatooine', 'planet descriptions', 'environments')",
                        }
                    },
                    "required": ["query"],
                },
            ),
            T3RNTool(
                name="getRagBattleDetails",
                function=db_rag_get_battle_details,
                description="Search battle information",
                system_prompt="""
Tool geRagtBattleDetails allows the droid to retrieve information about battles in the game.
You can use this tool when user asks about:
* Historical battles or conflicts in the game world
* Information about specific battle scenarios
* Strategies for approaching particular battle encounters
* Details about famous battles or war events in the lore
You should not use this tool when:
* User asks about general gameplay mechanics not related to battles
* User asks about individual champion abilities (use champion tools instead)
* User is engaged in casual conversation
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for battle information (e.g., 'famous battles', 'war strategies', 'conflicts')",
                        }
                    },
                    "required": ["query"],
                },
            ),
            T3RNTool(
                name="getLoreDetails",
                function=db_get_lore_details,
                description="Get lore information from database",
                system_prompt="""
Tool getLoreDetails allows the droid to retrieve lore and background information about champions.
You can use this tool when user asks about:
* The backstory or history of a specific champion
* Lore relationships between characters
* Character origins or background information
* Detailed narrative context for a champion
Examples:
* "Give me a report on Luke Skywalker" use getLoreDetails("Luke Skywalker")
* "I want a report about Darth Vader" use getLoreDetails("Darth Vader")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "champion_name": {
                            "type": "string",
                            "description": "Name of the champion to get lore details for",
                        }
                    },
                    "required": ["champion_name"],
                },
            ),
            T3RNTool(
                name="getBattleDetails",
                function=db_get_battle_details,
                description="Get detailed battle information including battle summary, participants, objectives, and strategic analysis",
                system_prompt="""
Tool getBattleDetails allows the droid to retrieve detailed information about battles.
You can use this tool when user asks about:
* Specific battles or conflicts in the game's lore
* Historical battles and their significance
* Battle locations and key participants
* Battle outcomes and consequences
Examples:
* "Tell me about the Battle of Endor" use getBattleDetails("Battle of Endor")
* "Get details about Death Star battle" use getBattleDetails("Death Star")
* "Show me info about Hoth battle" use getBattleDetails("Hoth")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for battle information (e.g., specific battle names, conflicts, or battle-related topics)",
                        }
                    },
                    "required": ["query"],
                },
            ),
        ]
