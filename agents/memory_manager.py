import json
import os
import textwrap
from typing import List, TypedDict
from venv import logger

import markdown
import openai
from bs4 import BeautifulSoup
from openai.types.chat import ChatCompletionMessageParam

from agents.base_agent import chat_completion_to_content_str
from channel_logger import ChannelLogger
from workload_config import AGENT_CONFIG


class ConversationMemory(TypedDict):
    summary: str | None
    running_messages: List["ChatCompletionMessageParam"]
    old_messages: List["ChatCompletionMessageParam"]
    last_user_message: str | None


class MemoryManager:
    def __init__(self, channel_logger: "ChannelLogger"):
        self.max_exchanges = AGENT_CONFIG.getint("MemoryManager", "max_exchanges")
        self.max_summary_size = AGENT_CONFIG.getint("MemoryManager", "max_summary_size")
        self.summary_target_after_llm = AGENT_CONFIG.getint("MemoryManager", "summary_target_after_llm")
        self.summary_temperature = AGENT_CONFIG.getfloat("MemoryManager", "summary_temperature")

        self.llm_summarization_count = 0

        self.openai_client = None

        self.memory = self.initialize_session_memory()

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
            except Exception:
                self.openai_client = None
        else:
            logger.warning("Memory Menager will not use openAI for summarization (No API KEY)")

        self.channal_logger: ChannelLogger = channel_logger

    def initialize_session_memory(
        self,
    ) -> ConversationMemory:
        """Initialize simple conversation memory structure"""
        return {
            "running_messages": [],
            "old_messages": [],
            "summary": "",
            "last_user_message": None,
        }

    def prepare_messages_for_agent(self) -> List["ChatCompletionMessageParam"]:
        # Build messages for LLM
        messages: List["ChatCompletionMessageParam"] = []

        # Add all exchanges from the list
        messages.extend(self.memory["running_messages"])

        return messages

    def last_exchange(self) -> List["ChatCompletionMessageParam"]:
        messages = (
            self.memory["old_messages"]
            + self.memory["running_messages"]
            + [
                {
                    "role": "user",
                    "content": self.memory["last_user_message"] or "",
                }
            ]
        )

        if len(messages) == 1:
            return [messages[0]]

        last_assistant_idx = None
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "assistant":
                last_assistant_idx = i
                break

        if last_assistant_idx is None:
            return []

        for i in range(last_assistant_idx - 1, -1, -1):
            if messages[i]["role"] == "user":
                return [
                    messages[i],
                    messages[last_assistant_idx],
                ]

        return []

    def finalize_current_cycle(self, messages: List["ChatCompletionMessageParam"]) -> None:
        # Update running messages with current state
        self.memory["running_messages"] = messages

        total_size = sum(len(str(msg)) for msg in messages)

        # Sumarization logic
        while len(messages) > self.max_exchanges or total_size > self.max_summary_size:
            messages_to_summarize = messages[: self.max_exchanges // 2]
            remaining_messages = messages[self.max_exchanges // 2 :]

            summary_text = ""
            for msg in messages_to_summarize:
                role = msg["role"]
                summary_text += f"{role}: {self._clean_markdown(chat_completion_to_content_str(msg))}\n"

            if self.memory["summary"]:
                summary_text = f"{self.memory['summary']}\n\n{summary_text}"

            compressed_summary = self._summarize_text(summary_text, self.summary_target_after_llm)
            self.memory["summary"] = compressed_summary

            self.memory["running_messages"] = remaining_messages
            self.memory["old_messages"].extend(messages_to_summarize)

            messages = remaining_messages

            total_size = sum(len(str(msg)) for msg in messages)

            self.llm_summarization_count += 1

    def _summarize_text(self, text: str, target_size: int) -> str:
        if self.openai_client is None:
            return textwrap.shorten(text, width=target_size)

        try:
            # Calculate approximate character count (rough estimate: 1 byte per char for English)
            target_chars = int(target_size * 0.8)  # Conservative estimate

            # Use OpenAI for intelligent summarization
            prompt = (
                f"Summarize the following text to approximately {target_chars} characters while preserving key information. Be concise:\n\n{text}"
            )

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates very concise summaries. Be extremely brief.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.summary_temperature,
                max_completion_tokens=int(target_chars / 2),
            )

            if response.choices[0].message.content is None:
                logger.error("Empty response from OpenAI summarization")
                return textwrap.shorten(text, width=target_size)

            summary = response.choices[0].message.content.strip()

            summary = textwrap.shorten(summary, width=target_size)

            return summary

        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return textwrap.shorten(text, width=target_size)

    def _clean_markdown(self, text: str) -> str:
        html = markdown.markdown(text)
        return BeautifulSoup(html, features="html.parser").get_text()

    def log_memory(self):
        try:
            messages = self.prepare_messages_for_agent()
            old_messages = self.memory["old_messages"]
            summary = self.memory["summary"]

            self.channal_logger.log_to_memory(
                f"Memory Summary: {summary}\n"
                f"Running Messages: {len(messages)}\n"
                f"All Messages: {len(old_messages)}\n"
                "Messages:\n"
                f"{json.dumps(messages, indent=2)}\n"
                f"Old Messages:\n{json.dumps(old_messages, indent=2)}"
            )
        except Exception as e:
            self.channal_logger.log_to_logs(f"❌ Failed to log memory: {str(e)}")

    def __dict__(self) -> ConversationMemory:
        return self.memory