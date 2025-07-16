
from abc import ABC, abstractmethod
from typing import List
from openai.types.chat import (
    ChatCompletionMessageParam,
)
from channel_logger import ChannelLogger
from session import Session
from tools_functions import T3RNTool


class T3RNModule(ABC):
    def __init__(self, channel_logger: ChannelLogger):
        self.channel_logger = channel_logger
    
    def inject_once_and_log(self, session: 'Session'):
        injected_messages = self.inject_once(session)
        if len(injected_messages) > 0:
            self.channel_logger.log_to_logs(f"Module {self.__class__.__name__} injected {len(injected_messages)} messages on begining") 
        return injected_messages

    def inject_before_user_message_and_log(self, session: 'Session'):
        injected_messages = self.inject_before_user_message(session)
        if len(injected_messages) > 0:
            self.channel_logger.log_to_logs(f"Module {self.__class__.__name__} injected {len(injected_messages)} messages before user") 
        return injected_messages

    def inject_after_user_message_and_log(self, session: 'Session'):
        injected_messages = self.inject_after_user_message(session)
        if len(injected_messages) > 0:
            self.channel_logger.log_to_logs(f"Module {self.__class__.__name__} injected {len(injected_messages)} messages after user") 
        return injected_messages

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