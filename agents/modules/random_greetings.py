from typing import List

from openai.types.chat import ChatCompletionMessageParam

from agents.modules.module import T3RNModule
from session import Session
from tools.db_get_random_greetings import db_get_random_greetings_text


class RandomGreetings(T3RNModule):
    def inject_start(self, session: Session) -> List[ChatCompletionMessageParam]:
        memory = session.get_memory().memory

        if len(memory["old_messages"]) + len(memory["running_messages"]) > 1:
            return []

        random_greetings = db_get_random_greetings_text()

        response = f"Droid, the conversation is about to start. You can use the following greetings to start the conversation once: \n {random_greetings}"

        injection_messages: List[ChatCompletionMessageParam] = [
            {
                "role": "developer",
                "content": response,
            }
        ]

        return injection_messages
