from abc import ABC
from typing import Iterable, List

from openai.types.chat import (
    ChatCompletionMessageParam,
)

from channel_logger import ChannelLogger
from session import Session
from tools_functions import T3RNTool


class T3RNModule(ABC):
    """
    This is an abstraction over T3RN modules. It can be used to inject messages into the chat session at various points.
    It is designed to be used with the T3RN agent system, allowing for modular message injection into the chat flow.

    # Callbacks order
    The order of injection is important:
    1. `before_user_message` - it is called on the beginning of execution
    2. `define_tools` - it is called to define tools available for the agent
    2. `inject_start` - it collects messages that will be injected at the start of the every session
    3. `inject_before_user_message` - it collects messages that will be injected before the user message
    4. `inject_after_user_message` - it collects messages that will be injected after the user message
    5. `after_user_message` - it is called after the user message is processed, allowing for modifications to the session.

    # Prompt structure
    ```
    <SYSTEM_PROMPT>
    <inject_start>
    <MESSAGE_HISTORY>
    <inject_before_user_message>
    <USER_MESSAGE>
    <inject_after_user_message>
    <LLM_RESPONSES>
    ```
    """

    def __init__(self, channel_logger: ChannelLogger):
        self.channel_logger = channel_logger

    def inject_start_and_log(self, session: "Session"):
        injected_messages = self.inject_start(session)
        if len(injected_messages) > 0:
            self.channel_logger.log_to_logs(
                f"Module {self.__class__.__name__} injected {len(injected_messages)} messages on begining"
            )
        return injected_messages

    def inject_before_user_message_and_log(self, session: "Session"):
        injected_messages = self.inject_before_user_message(session)
        if len(injected_messages) > 0:
            self.channel_logger.log_to_logs(
                f"Module {self.__class__.__name__} injected {len(injected_messages)} messages before user"
            )
        return injected_messages

    def inject_after_user_message_and_log(self, session: "Session"):
        injected_messages = self.inject_after_user_message(session)
        if len(injected_messages) > 0:
            self.channel_logger.log_to_logs(
                f"Module {self.__class__.__name__} injected {len(injected_messages)} messages after user"
            )
        return injected_messages

    def before_user_message(self, session: "Session") -> "Session":
        """
        This method is called on the beginning of the session. It can modify the session.
        """
        return session

    def after_user_message(self, session: "Session") -> "Session":
        """
        This method is called after the processing the user message. It can modify the session.
        """
        return session

    def inject_start(self, session: "Session") -> List["ChatCompletionMessageParam"]:
        """
        Inject on the begining of the session (after system prompt)
        """
        return []

    def inject_before_user_message(
        self,
        session: "Session",
    ) -> List["ChatCompletionMessageParam"]:
        """
        Return messages that should be injected *before* user message.
        """
        return []

    def inject_after_user_message(
        self,
        session: "Session",
    ) -> List["ChatCompletionMessageParam"]:
        """
        Return messages to be injected *after* the user message.
        """
        return []

    def define_tools(self, session: "Session") -> Iterable["T3RNTool"]:
        """
        Should define tools that are available for the agent.
        """
        return []


def build_system_instructions_from_tools(tools: List["T3RNTool"]) -> str:
    """
    Build system instructions from the tools.
    """
    if not tools:
        return ""

    instructions = "You have access to the following tools:\n"
    for tool in tools:
        instructions += f"# {tool.name}:\n{tool.system_prompt}\n"
    return instructions

def get_tool_by_name(
    tools: List["T3RNTool"], tool_name: str
) -> "T3RNTool | None":
    for tool in tools:
        if tool.name == tool_name:
            return tool
    return None