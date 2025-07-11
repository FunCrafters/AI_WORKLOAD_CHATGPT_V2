
from abc import ABC, abstractmethod
from typing import List, Tuple, Union
from openai.types.chat import (
    ChatCompletionMessageParam,
)

from session import Session

class T3RNModule(ABC):
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