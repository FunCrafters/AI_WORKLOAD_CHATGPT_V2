from typing import List
from openai.types.chat import ChatCompletionMessageParam
from agents.modules.module import T3RNModule
from session import Session
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
            )
        ]
