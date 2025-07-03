#!/usr/bin/env python3
"""
Simple Fallback Agent
Emergency agent that provides basic fallback responses
"""

import random
from agents.base_agent import Agent, AgentContext, AgentResult
from agents.agent_prompts import T3RN_MALFUNCTION_MESSAGES

class SimpleFallbackAgent(Agent):
    """Simple emergency agent that provides basic fallback responses"""
    
    def __init__(self):
        super().__init__()
    
    def get_system_prompt(self, context: AgentContext) -> str:
        """Get system prompt for fallback mode"""
        return self.build_prompt('CHARACTER_BASE_T3RN')
    
    def execute(self, context: AgentContext, channel_logger) -> AgentResult:
        """Execute SimpleFallbackAgent with minimal processing"""
        
        channel_logger.log_to_logs("🛡️ SimpleFallbackAgent starting error recovery")
        
        original_query = context.original_user_message or "your request"
            
        # Select a random T3RN malfunction message
        fallback_response = random.choice(T3RN_MALFUNCTION_MESSAGES)
            
        channel_logger.log_to_logs("✅ SimpleFallbackAgent completed successfully")
        channel_logger.log_to_logs("💭 SIMPLE FALLBACK: System error occurred, providing T3RN malfunction response")
            
        result = AgentResult()
        result.final_answer = fallback_response
            
        return result
            