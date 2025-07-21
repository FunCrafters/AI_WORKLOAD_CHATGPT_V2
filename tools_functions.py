from dataclasses import dataclass
from typing import Any, Callable

from openai.types.chat import ChatCompletionToolParam
from openai.types.shared_params.function_parameters import FunctionParameters

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
# - getBossInfo() # might be merge
#   - db_rag_get_boss_details
#   - if fails to find anything call other function wih information: No Boss Info found,
#   - and should Call RAG databse for more information
# - searchDatabases()
#   - db_rag_get_general_knowledge # treshold_1
#   - db_rag_get_location_details # trehdold_2
#   - if failed to find call <getBattleDetails()> # Might
# - getBattleDetails()
#   - db_rag_get_battle_details
#   - db_get_battle_details
#   - db_get_battle_details_byid
# - getUIInformation()
#   - db_get_screen_context_help()
#   - db_get_ux_details()
# - compareChampions() # turn off later
# - Rest of the tools as they are. Or left for merge later
#
# Tools that should be called when proper embedding found in DB 'proactive' tools.
# Search after every querry BEFORE LLM generation.
# - db_rag_get_smalltalk
# - db_rag_get_champion_details (high treshold)
# - db_rag_get_boss_details (high treshold)
# - db_rag_get_general_knowledge
# - db_rag_get_gameplay_details (high treshold)


@dataclass
class T3RNTool:
    """
    Represents a tool function for the T3RN agent.
    This tool can be dependent on current session of LLM agent.
    """

    name: str
    function: Callable[..., dict | str]
    description: str
    system_prompt: str
    parameters: FunctionParameters

    def __call__(self, *args: Any, **kwds: Any) -> dict | str:
        return self.function(*args, **kwds)

    def get_function_schema(self) -> "ChatCompletionToolParam":
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
