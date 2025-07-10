#!/usr/bin/env python3
"""
Simple Fallback Agent
Emergency agent that provides basic fallback responses
"""

import random
from agents.base_agent import Agent, AgentContext, AgentResult
from agents.agent_prompts import T3RN_MALFUNCTION_MESSAGES
from channel_logger import ChannelLogger
from session import Session

class SimpleFallbackAgent(Agent):
    """Simple emergency agent that provides basic fallback responses"""
    
    def __init__(self, session: 'Session', channel_logger: 'ChannelLogger'):
        super().__init__(session, channel_logger)
    
    def get_system_prompt(self, context: AgentContext) -> str:
        return self.build_prompt('CHARACTER_BASE_T3RN')
    
    def execute(self, user_message: str) -> AgentResult:        
        self.channel_logger.log_to_logs("🛡️ SimpleFallbackAgent starting error recovery")
                    
        fallback_response = random.choice(T3RN_MALFUNCTION_MESSAGES)
            
        self.channel_logger.log_to_logs("✅ SimpleFallbackAgent completed successfully")
        self.channel_logger.log_to_logs("💭 SIMPLE FALLBACK: System error occurred, providing T3RN malfunction response")
            
        result = AgentResult()
        result.final_answer = fallback_response
            
        return result
            