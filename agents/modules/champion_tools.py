from typing import List
from agents.modules.module import T3RNModule
from session import Session
from tools.db_get_champion_details import db_get_champion_details
from tools.db_rag_get_boss_details import db_rag_get_boss_details
from tools.db_rag_get_champion_details import db_rag_get_champion_details
from tools_functions import T3RNTool


def getChampionsDetails(
    champion_name: str, prefer_lore: bool=False, session: Session | None = None
) -> dict:
    champion = db_get_champion_details(champion_name)
    boss = db_rag_get_boss_details(champion_name)
    champ_rag = db_rag_get_champion_details(champion_name)

    return dict()


class ChampionTools(T3RNModule):
    def define_tools(self, session: "Session") -> List["T3RNTool"]:
        return [
            T3RNTool(
                name="getChampionsDetails",
                function=lambda champ_name, lore: getChampionsDetails(
                    champ_name, lore, session
                ),
                description="Get details about a specific champion from the game. ",
                system_prompt="""
Tool getChampionsDetails allows the droid to retrieve information about a specific champion in the game.
It will prioritize providing usefull information about game mechanics, stats abilities.
If it wont find any information about the champion it will return informations about lore, characters, places or events that are related to the champion.
Use the tool when the user asks for:
* Information about a specific champion, especially if they ask for details about information related to battle, game or mechanics.
* When user wants to know about champion abilities, stats, lore or any other.
* When user asks about champion in context of the current screen or game state. For example if champion is visible or selected in the game.
When to not use this tool:
* When the character is not an champion in the game.
* When the user specifically asks for smalltalk or casual conversation topics related to the champion.
* Revelant information is already provided in context of the conversation.
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "champion_name": {
                            "type": "string",
                            "description": "Exact name of the champion to get details for",
                        },
                        "prefer_lore": {
                            "type": "boolean",
                            "description": "If true the tool will prefer to return information about character rather than game mechanics, stats or abilities.",
                        },
                        "required": ["champion_name"],
                    },
                },
            ),
            T3RNTool(
                name="getRAGCharacterDetails",
                function=lambda champ_name, lore: getChampionsDetails(
                    champ_name, lore, session
                ),
                description="Get lore details about a specific champion from the game using natural language (Questions)",
                system_prompt="""
Tool getRAGCharacterDetails allows the droid to retrieve information about a specific champion in the game using natural language.
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "champion_name": {
                            "type": "string",
                            "description": "Exact name of the champion to get details for",
                        },
                        "prefer_lore": {
                            "type": "boolean",
                            "description": "If true the tool will prefer to return information about character rather than game mechanics, stats or abilities.",
                        },
                        "required": ["champion_name"],
                    },
                },
            ),
        ]
