from typing import List

from openai.types.chat import ChatCompletionMessageParam

from agents.modules.module import T3RNModule
from session import Session
from tool import T3RNTool
from tools.db_get_ux_details import db_get_screen_details


class ScreenContextInjector(T3RNModule):
    def inject_start(self, session: Session) -> List[ChatCompletionMessageParam]:
        injection_messages = []
        gamestate = session.gamestate()
        try:
            screen_details = gamestate.build_prompt()
            injection_messages.append(
                {
                    "role": "developer",
                    "content": f"""
User currently is on the following screen:
{screen_details}
You can use getScreenDetails() tool to get more information about the screen.
Here are possible arguments for the tool:
{gamestate.get_keys()}
""",
                }
            )
        except Exception:
            injection_messages.append(
                {
                    "role": "developer",
                    "content": """
User currently is on the unknown screen.  
""",
                }
            )

        return injection_messages

    def define_tools(self, session: Session) -> List[T3RNTool]:
        return [
            T3RNTool(
                name="getScreenDetails",
                function=lambda query: db_get_screen_details(query, session),
                description="Get details about the current screen or UI element",
                system_prompt="""
Tool getScreenDetails allows the droid to retrieve information about the user interface.
You can use this tool when user asks about:
* How to navigate the interface
* What different UI elements mean
* How to perform specific actions in the interface
* Information about game menus, buttons, or screens
You should not use this tool when:
* User asks about gameplay mechanics not related to the interface
* User asks about lore, characters, or story elements
Argument should use the name of the UI element or screen. 
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
            )
        ]
