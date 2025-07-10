#!/usr/bin/env python3
"""
Fallback Agent
Simplified agent without loops or tools, uses only RAG knowledge
"""

import json
import os
import time
from typing import List, Dict, Any, Optional
from openai.types.chat import ChatCompletionMessageParam
from channel_logger import ChannelLogger
from session import Session
from tools.db_rag_get_general_knowledge import db_rag_get_general_knowledge

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from agents.base_agent import Agent, AgentContext, AgentResult

class FallbackAgent(Agent):
    """Simplified fallback agent using only RAG knowledge"""
    
    def __init__(self, session: 'Session', channel_logger: 'ChannelLogger'):
        super().__init__(session, channel_logger)
        
        self.openai_client: Optional[openai.OpenAI] = None

        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
    
    def get_system_prompt(self,) -> str:
        """Simple system prompt for fallback"""
        return self.build_prompt(
            'CHARACTER_BASE_T3RN',
            'GAME_CONTEXT', 
            'CONTENT_RESTRICTIONS',
        )

    
    def call_llm(self, messages: List['ChatCompletionMessageParam']) -> Any:
        """Simple LLM call without tools"""
        
        if self.openai_client is None:
            raise Exception("OpenAI not available for FallbackAgent")
        
        try:
            start_time = time.time()
            
            response = self.openai_client.chat.completions.create(
                model='gpt-4.1-mini',
                messages=messages,
                temperature=0.5,
                max_tokens=1000
            )
            
            elapsed_time = time.time() - start_time
            
            # Log call info
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0
            
            self.channel_logger.log_to_logs(f"⚡ FallbackAgent completed in {elapsed_time:.3f}s ({prompt_tokens}+{completion_tokens}={total_tokens} tokens)")
            
            return response
            
        except Exception as e:
            self.channel_logger.log_to_logs(f"❌ FallbackAgent LLM error: {str(e)}")
            raise
    
    def execute(self, user_message: str) -> AgentResult:
        """Execute FallbackAgent with RAG knowledge only"""
        
        self.channel_logger.log_to_logs("🛡️ FallbackAgent starting with RAG knowledge")
        
        try:            
            # Pre-load RAG data
            general_knowledge = db_rag_get_general_knowledge(user_message)
            self.channel_logger.log_to_logs(f"🔍 FallbackAgent pre-loaded RAG data for: '{user_message}'")
            
            # Prepare simple messages
            messages = [{
                "role": "system",
                "content": self.get_system_prompt()
            }] # type: List[ChatCompletionMessageParam]
            
            if general_knowledge:
                messages.append({
                    "role": "system", 
                    "content": f"Available knowledge: {general_knowledge}"
                })
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            self.channel_logger.log_to_logs("🤖 FallbackAgent calling ChatGPT-4o-mini without tools")
            response = self.call_llm(messages)
            
            response_content = response.choices[0].message.content or "No response generated"
            
            self.channel_logger.log_to_logs("✅ FallbackAgent completed successfully")
            
            messages.append({
                "role": "assistant",
                "content": response_content
            })

            result = AgentResult()
            result.final_answer = response_content
            result.error_content = ""
            
            return result
            
        except Exception as e:
            raise Exception(f"Fallback Agent logic error")
