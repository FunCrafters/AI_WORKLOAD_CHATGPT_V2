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
    
    # TODO CHECK IF THIS IS HELPFULL AT ALL...
    def _log_llm_call_to_prompts_channel(self, messages: List['ChatCompletionMessageParam'], tools: Optional[List] = None, 
                                       use_json: bool = False):
        try:            
            agent_name = self.__class__.__name__
            
            # Extract system prompt (first message)
            system_prompt = ""
            if messages and messages[0].get('role') == 'system':
                system_prompt = messages[0]['content'] # TODO content is more complex than that. There should be function 'parse content' that will handle all cases and always return str
            
            # Format messages (with intelligent length limits for readability)
            formatted_messages = []
            for msg in messages:
                content = msg.get('content', '')
                
                # Handle None content
                if content is None:
                    content = '[None]'
                
                # Special handling for different message types
                if msg.get('role') == 'function':
                    # Tool results - show basic info only
                    content = f"[Tool result: {len(str(content))} chars]"
                elif content and content.startswith("Tool execution results:"):
                    content = textwrap.shorten(content, width=200, placeholder="[...]\n[truncated - tool results]")
                elif len(content) > 300:
                    content = textwrap.shorten(content, width=300)
                
                formatted_msg = {
                    "role": msg['role'],
                    "content": content
                }

                if 'tool_calls' in msg:
                    formatted_msg['tool_calls'] = "[tool_calls_present]"
                if 'function_call' in msg:
                    formatted_msg['function_call'] = {       
                        "name": msg['function_call']['name'], 
                        "arguments": "[arguments_present]"
                    }
                if 'name' in msg:
                    formatted_msg['name'] = msg['name']
                formatted_messages.append(formatted_msg)
            
            # Create complete log (action_id will be added by channel_logger)
            prompt_log = f"""{agent_name} | Base Agent
                === CALL PARAMETERS ===
                Model: llama3.1:8b
                Format: {'json' if use_json else 'standard'}
                Keep-alive: 60m

                === MESSAGES TO LLM ===
                {json.dumps(formatted_messages, indent=2, ensure_ascii=False)}

                === SYSTEM PROMPT ===
                {system_prompt}
                ---
                """.strip()
            self.channel_logger.log_to_prompts(prompt_log)
            
        except Exception as e:
            self.channel_logger.log_to_logs(f"❌ Failed to log to Prompts channel: {str(e)}")



    def build_prompt(self, *fragments) -> str:
        # Map fragment names to actual fragments
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
    
