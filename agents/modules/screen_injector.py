from typing import List

from openai.types.chat import ChatCompletionMessageParam

from agents.modules.module import T3RNModule
from session import Session


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
