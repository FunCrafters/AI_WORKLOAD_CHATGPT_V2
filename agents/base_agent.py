#!/usr/bin/env python3
"""
Base Agent Class
Foundation for all agents in the agent-based architecture
"""

import logging
import json
import textwrap
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from openai.types.chat import ChatCompletionMessageParam
from channel_logger import ChannelLogger
from session import Session
from agents.agent_prompts import (
    CHARACTER_BASE_T3RN, CHARACTER_BASE_T4RN, GAME_CONTEXT, CONTENT_RESTRICTIONS, T3RN_INTRODUCTION,
    JSON_FORMAT,MOBILE_FORMAT,
    QUESTION_ANALYZER_INITIAL_TASK, 
    QUESTION_ANALYZER_RULES, QUESTION_ANALYZER_TOOLS, CHAMPIONS_AND_BOSSES,
    TOOL_RESULTS_ANALYSIS
)


def chat_completion_to_content_str(content: ChatCompletionMessageParam) -> str:
    content_str = content.get("content", None)

    if content_str is None:
        return ""

    if isinstance(content_str, str):
        return content_str
    
    
    return str(''.join([str(x) for x in content_str]))


logger = logging.getLogger("Base Agent")

class AgentResult:
    def __init__(self):
        self.final_answer: Optional[str] = None
        self.user_message: str = ""
        self.error_content: str = ""
        self.missing_information: Optional[List[str]] = None

class Agent(ABC):
    def __init__(self, session: 'Session', channel_logger: 'ChannelLogger'):
        self.tools = []
        self.session_data: 'Session' = session
        self.channel_logger: 'ChannelLogger' = channel_logger
        # TODO is this correct? Trace back to session_data if it can be guaranteed to have memory manager
        if self.session_data.memory_manager is None: 
            raise ValueError("Session must have a memory manager initialized")
        
        self.memory_manager = self.session_data.memory_manager

    @abstractmethod
    def get_system_prompt(self,) -> str:
        """Get system prompt for this agent"""
        pass
    
    @abstractmethod
    def execute(self, context: str) -> AgentResult:
        """Execute the agent with given context"""
        pass
    
    def _log_state(self, messages: List['ChatCompletionMessageParam']|List[Any]):
        try:
            agent_name = self.__class__.__name__

            session = self.session_data
            mm = session.memory_manager

            short_messages = [
                {
                    **message,
                    'content': textwrap.shorten(chat_completion_to_content_str(message), width=500)
                }
                for message in messages
            ]

            state_log = {
                "agent": agent_name,
                "session_id": session.session_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "message_count": session.message_count,
                "channel": session.channel,
                "message_id": session.message_id,
                "action_id": session.action_id,
                "text_snippet": (session.user_message[:100] + '...') if session.user_message and len(session.user_message) > 100 else session.user_message,
                "memory_summary": {
                    "llm_summarization_count": mm.llm_summarization_count

                } if mm else "No memory manager",
                "messages": messages, 
                "json_data_keys": list(session.json_data.keys()) if session.json_data else []
            }

            pretty_log = f"""
=== AGENT STATE DUMP ===
Agent: {agent_name}
Session ID: {state_log['session_id']}
Created At: {state_log['created_at']}
Last Activity: {state_log['last_activity']}
Msg Count: {state_log['message_count']} | Action ID: {state_log['action_id']}
Channel: {state_log['channel']} | Msg ID: {state_log['message_id']}
Text Snippet: {state_log['text_snippet']}

=== Messages ===
{json.dumps(short_messages, indent=2)}
""".strip()

            self.channel_logger.log_to_prompts(pretty_log)

        except Exception as e:
            self.channel_logger.log_to_logs(f"❌ Failed to log state: {str(e)}")

    def build_prompt(self, *fragments) -> str:
        fragment_map = {
            'CHARACTER_BASE_T3RN': CHARACTER_BASE_T3RN,
            'CHARACTER_BASE_T4RN': CHARACTER_BASE_T4RN,
            'GAME_CONTEXT': GAME_CONTEXT,
            'CONTENT_RESTRICTIONS': CONTENT_RESTRICTIONS,
            'T3RN_INTRODUCTION': T3RN_INTRODUCTION,
            'JSON_FORMAT': JSON_FORMAT,
            'MOBILE_FORMAT': MOBILE_FORMAT,
            'QUESTION_ANALYZER_INITIAL_TASK': QUESTION_ANALYZER_INITIAL_TASK,
            'CHAMPIONS_AND_BOSSES': CHAMPIONS_AND_BOSSES,
            'QUESTION_ANALYZER_RULES': QUESTION_ANALYZER_RULES,
            'QUESTION_ANALYZER_TOOLS': QUESTION_ANALYZER_TOOLS,
            'TOOL_RESULTS_ANALYSIS': TOOL_RESULTS_ANALYSIS
        }
        
        prompt_parts = []
        for fragment in fragments:
            if isinstance(fragment, str):
                if fragment in fragment_map:
                    prompt_parts.append(fragment_map[fragment])
                else:
                    # Treat as custom text
                    prompt_parts.append(fragment)
            else:
                # Convert to string
                prompt_parts.append(str(fragment))
        
        return '\n\n'.join(prompt_parts)

    def get_config(self) -> Dict[str, Any]:
        return {
            'class_name': self.__class__.__name__
        }
    
