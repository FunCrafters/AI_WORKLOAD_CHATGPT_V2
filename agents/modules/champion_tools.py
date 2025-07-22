import json
from typing import List

from agents.modules.module import T3RNModule
from session import Session
from tools.db_get_champion_details import db_get_champion_details
from tools.db_get_champions_list import db_get_champions_list_text
from tools.db_rag_get_boss_details import db_rag_get_boss_details
from tools.db_rag_get_champion_details import db_rag_get_champion_details
from tools_functions import T3RNTool


def getChampionsDetails(champion_name: str, prefer_lore: bool = False, session: Session | None = None) -> str:
    champion = db_get_champion_details(champion_name)
    boss = db_rag_get_boss_details(champion_name)
    champ_rag = db_rag_get_champion_details(champion_name)

    # TODO championMechanics
    # TODO make it session-aware
    if session:
        _exch = session.get_memory().last_exchange()

    response = ""

    if champion["status"] == "success":
        response += f"{json.dumps(champion)}\n"
    if boss["status"] == "success":
        response += f"{json.dumps(boss)}\n"
    if champ_rag["status"] == "success":
        response += f"{json.dumps(champ_rag)}\n"

    if champion["status"] != "success":
        champ_list = db_get_champions_list_text()
        return json.dumps(
            {
                "status": "error",
                "message": f"No details found for champion '{champion_name}'. List of available champions: {champ_list}\n Galactic databased found only few snippets about this champion, but it seems to be not a champion: {response}",
                "llm_guidance": "You can ask if this is mistake, try to use other tool or use available informations.",
                "champion_name": champion_name,
            }
        )
    else:
        return response


class ChampionTools(T3RNModule):
    def define_tools(self, session: "Session") -> List["T3RNTool"]:
        return [
            T3RNTool(
                name="getChampionsDetails",
                function=lambda champion_name, prefer_lore=False: getChampionsDetails(champion_name, prefer_lore, session),
                description="Get details about a specific champion from the game. ",
                system_prompt="""
Tool getChampionsDetails allows the droid to retrieve information about a specific champion in the game.
It will prioritize providing usefull information about game mechanics, stats abilities.
If it wont find any information about the champion it will return informations about lore, characters, places or events that are related to the champion.
You can force more lore related information by setting prefer_lore to true.
Use the tool when the user asks for:
* Information about a specific champion, especially if they ask for details about information related to battle, game or mechanics.
* When user wants to know about champion abilities, stats, lore or any other.
* When user asks about champion in context of the current screen or game state. For example if champion is visible or selected in the game.
When to not use this tool:
* When the character is not an champion in the game.
* When the user specifically asks for smalltalk or casual conversation topics related to the champion.
* Revelant information is already provided in context of the conversation.
Examples:
* "Tell me everything about Han Solo" use getChampionsDetails("Han Solo")
* "Get full details for Luke Skywalker"  use getChampionsDetails("Luke Skywalker")
* "Who is Chewbacca" use getChampionsDetails("Chewbacca", prefer_lore=True)
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
                    },
                    "required": ["champion_name"],
                },
            ),
            T3RNTool(
                name="getRAGCharacterDetails",
                function=lambda champion_name: db_rag_get_champion_details(champion_name),
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
                    },
                    "required": ["champion_name"],
                },
            ),
        ]
