from typing import List

from agents.modules.module import T3RNModule
from session import Session
from tools.db_compare_champions import db_compare_champions
from tools.db_find_champions_stronger_than import db_find_champions_stronger_than
from tools.db_find_strongest_champions import db_find_strongest_champions
from tools_functions import T3RNTool


class ChampionCompTools(T3RNModule):
    def define_tools(self, session: "Session") -> List["T3RNTool"]:
        return [
            T3RNTool(
                name="compareChampions",
                function=lambda champion_names, detailed=True: db_compare_champions(
                    champion_names=champion_names, detailed=detailed
                ),
                description="Compare two or more champions side by side with comprehensive analysis of stats, traits, roles, and recommendations.",
                system_prompt="""
Tool compareChampions allows the droid to compare multiple champions side by side with comprehensive analysis.
Use this tool when the user wants to:
* Compare abilities, stats, strengths, or weaknesses between two or more champions
* Determine which champion is better for specific situations or team compositions
* Get a side-by-side comparison of champion traits, roles, and effectiveness
* Analyze which champions complement each other in battle

Examples:
* "Compare Han Solo and Luke Skywalker" use compareChampions(["Han Solo", "Luke Skywalker"])
* "How do Darth Vader, Emperor Palpatine, and Kylo Ren compare?" use compareChampions(["Darth Vader", "Emperor Palpatine", "Kylo Ren"])
* "Which is better between Chewbacca and Boba Fett?" use compareChampions(["Chewbacca", "Boba Fett"])
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "champion_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of champion names to compare (minimum 2 required, maximum 5)",
                            "minItems": 2,
                            "maxItems": 5,
                        },
                        "detailed": {
                            "type": "boolean",
                            "description": "Whether to include detailed analysis (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["champion_names"],
                },
            ),
            T3RNTool(
                name="findStrongestChampions",
                function=lambda limit=10,
                rarity=None,
                affinity=None,
                class_type=None: db_find_strongest_champions(
                    limit=limit, rarity=rarity, affinity=affinity, class_type=class_type
                ),
                description="Find the strongest champions based on total power with optional trait filtering.",
                system_prompt="""
Tool findStrongestChampions allows the droid to identify the most powerful champions in the game with optional filtering.
Use this tool when the user wants to:
* Find the most powerful champions in the game overall
* Discover the strongest champions of a specific rarity (legendary, epic, rare, etc.)
* Identify powerful champions of a specific affinity (red, blue, green, yellow, purple)
* Find the strongest champions in a specific class (attacker, defender, support)
* Get recommendations for powerful champions to add to their roster

Examples:
* "Who are the strongest champions in the game?" use findStrongestChampions()
* "Show me the top 5 legendary champions" use findStrongestChampions(limit=5, rarity="legendary")
* "What are the best red attackers?" use findStrongestChampions(affinity="red", class_type="attacker")
* "List the 15 strongest defenders" use findStrongestChampions(limit=15, class_type="defender")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of top champions to return (default: 10, max: 50)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50,
                        },
                        "rarity": {
                            "type": "string",
                            "description": "Filter by rarity (legendary, epic, rare, uncommon, common)",
                            "enum": ["legendary", "epic", "rare", "uncommon", "common"],
                        },
                        "affinity": {
                            "type": "string",
                            "description": "Filter by affinity (red, blue, green, yellow, purple)",
                            "enum": ["red", "blue", "green", "yellow", "purple"],
                        },
                        "class_type": {
                            "type": "string",
                            "description": "Filter by class type (attacker, defender, support)",
                            "enum": ["attacker", "defender", "support"],
                        },
                    },
                    "required": [],
                },
            ),
            T3RNTool(
                name="findChampionsStrongerThan",
                function=lambda character_name,
                limit=20,
                rarity=None,
                affinity=None,
                class_type=None: db_find_champions_stronger_than(
                    character_name=character_name,
                    limit=limit,
                    rarity=rarity,
                    affinity=affinity,
                    class_type=class_type,
                ),
                description="Find champions stronger than a specified reference champion with optional trait filtering.",
                system_prompt="""
Tool findChampionsStrongerThan allows the droid to identify champions that are more powerful than a specified reference champion.
Use this tool when the user wants to:
* Find champions that are stronger than a specific champion they already have
* Discover upgrade options for their current champion roster
* Compare a champion's power level to others in the game
* Find stronger champions with similar traits (rarity, affinity, class)

Examples:
* "Who is stronger than Han Solo?" use findChampionsStrongerThan("Han Solo")
* "Find 10 champions better than Luke Skywalker" use findChampionsStrongerThan("Luke Skywalker", limit=10)
* "Show me legendary champions stronger than Chewbacca" use findChampionsStrongerThan("Chewbacca", rarity="legendary")
* "Are there any blue defenders better than Obi-Wan?" use findChampionsStrongerThan("Obi-Wan", affinity="blue", class_type="defender")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "character_name": {
                            "type": "string",
                            "description": "Name of the reference champion to compare against",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of stronger champions to return (default: 20, max: 50)",
                            "default": 20,
                            "minimum": 1,
                            "maximum": 50,
                        },
                        "rarity": {
                            "type": "string",
                            "description": "Filter by rarity (legendary, epic, rare, uncommon, common)",
                            "enum": ["legendary", "epic", "rare", "uncommon", "common"],
                        },
                        "affinity": {
                            "type": "string",
                            "description": "Filter by affinity (red, blue, green, yellow, purple)",
                            "enum": ["red", "blue", "green", "yellow", "purple"],
                        },
                        "class_type": {
                            "type": "string",
                            "description": "Filter by class type (attacker, defender, support)",
                            "enum": ["attacker", "defender", "support"],
                        },
                    },
                    "required": ["character_name"],
                },
            ),
        ]
