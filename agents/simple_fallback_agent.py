#!/usr/bin/env python3
"""
Simple Fallback Agent
Emergency agent that provides basic fallback responses
"""

import random
from typing import List

from openai.types.chat import ChatCompletionMessageParam

from agents.agent_prompts import T3RN_MALFUNCTION_MESSAGES
from agents.base_agent import Agent, AgentResult
from channel_logger import ChannelLogger
from session import Session


class SimpleFallbackAgent(Agent):
    def __init__(self, session: "Session", channel_logger: "ChannelLogger"):
        super().__init__(session, channel_logger)

    def get_system_prompt(self) -> str:
        return self.build_prompt("CHARACTER_BASE_T3RN")

    def execute(self, user_message: str) -> AgentResult:
        fallback_response = random.choice(T3RN_MALFUNCTION_MESSAGES)

        old_messages = self.memory_manager.prepare_messages_for_agent()
        response: List["ChatCompletionMessageParam"] = [
            {"role": "user", "content": user_message},
            {
                "role": "assistant",
                "content": fallback_response,
            },
        ]

        result = AgentResult(old_messages + response)

        return result
