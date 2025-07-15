
from abc import ABC, abstractmethod
from typing import List
from openai.types.chat import (
    ChatCompletionMessageParam,
)
from channel_logger import ChannelLogger
from session import Session
from tools_functions import T3RNTool


class T3RNModule(ABC):
    def __init__(self, channal_logger: ChannelLogger):
        self.channal_logger = channal_logger

    @abstractmethod
    def inject_once(self, session: 'Session') -> List['ChatCompletionMessageParam']:
        """
        Inject on the begining of the session (after system prompt)
        """
        pass

    @abstractmethod
    def inject_before_user_message(
        self, 
        session: 'Session',
    ) -> List['ChatCompletionMessageParam']:
        """
        Return messages that should be injected *before* user message.
        """
        pass

    @abstractmethod
    def inject_after_user_message(
        self, 
        session: 'Session',
    ) -> List['ChatCompletionMessageParam']:
        """
        Return messages to be injected *after* the user message.
        """
        pass

    def define_tools(self, session: 'Session') -> List['T3RNTool']:  
        return []