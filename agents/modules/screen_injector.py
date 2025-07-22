from typing import List

from openai.types.chat import ChatCompletionMessageParam

from agents.modules.module import T3RNModule
from session import Session
from tools.db_get_screen_context_help import db_get_screen_context_help
from tools.db_get_ux_details import db_get_ux_details
from tools_functions import T3RNTool


class ScreenContextInjector(T3RNModule):
    def inject_start(self, session: Session) -> List[ChatCompletionMessageParam]:
        injection_messages = []

        injection_messages.append(
            {
                "role": "assistant",
                "content": "I can see you're currently on a specific screen.",
            }
        )

        return injection_messages

    def define_tools(self, session: Session) -> List[T3RNTool]:
        return [
            T3RNTool(
                name="getUXDetails",
                function=db_get_ux_details,
                description="Search UX and interface information from database",
                system_prompt="""
Tool getUXDetails allows the droid to retrieve information about the user interface.
You can use this tool when user asks about:
* How to navigate the interface
* What different UI elements mean
* How to perform specific actions in the interface
* Information about game menus, buttons, or screens
You should not use this tool when:
* User asks about gameplay mechanics not related to the interface
* User asks about lore, characters, or story elements
Examples:
* "How do I access the inventory?" use getUXDetails("inventory")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for UX information (e.g., 'interface', 'menu', 'navigation')",
                        }
                    },
                    "required": ["query"],
                },
            ),
            T3RNTool(
                name="getScreenContextHelp",
                function=db_get_screen_context_help,
                description="Get contextual help for current screen/UI state",
                system_prompt="""
Tool getScreenContextHelp provides contextual help about the current screen or UI state.
You can use this tool when:
* User asks what they can do on the current screen
* User seems confused about the purpose of the current interface
Examples:
* "What can I do here?" use getScreenContextHelp("what to do in the game")
""",
                parameters={
                    "type": "object",
                    "properties": {
                        "user_question": {
                            "type": "string",
                            "description": "User's question about the current screen/interface (e.g., 'where am I?', 'what can I do here?', 'how to use this?')",
                        }
                    },
                    "required": ["user_question"],
                },
            ),
        ]
