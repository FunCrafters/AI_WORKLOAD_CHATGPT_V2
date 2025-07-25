from typing import List

from openai.types.chat import ChatCompletionMessageParam

from agents.modules.module import T3RNModule
from session import Session


class SummaryInjector(T3RNModule):
    def inject_start(self, session: Session) -> List[ChatCompletionMessageParam]:
        summary = session.get_memory().memory["summary"]

        injection_messages = []

        if summary:
            injection_messages.append(
                {
                    "role": "developer",
                    "content": f"Previous conversation summary: {summary}",
                }
            )

        return injection_messages
