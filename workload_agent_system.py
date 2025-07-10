#!/usr/bin/env python3
"""
Agent-Based LLM System
New agent-based architecture for processing user messages
"""

import time
import logging
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING, Type

# Import agent classes
from agents.base_agent import Agent, AgentContext, AgentResult
from agents.simple_fallback_agent import SimpleFallbackAgent
from agents.t3rn_agent import T3RNAgent
from agents.fallback_agent import FallbackAgent
from agents.memory_manager import MemoryManager
from channel_logger import ChannelLogger
from session import Session
import random
from agents.agent_prompts import T3RN_MALFUNCTION_MESSAGES


# Logger
logger = logging.getLogger("Agent System")

#TODO Agent stack should be in Agent Dir
class AgentStack:
    """Manages the stack of agents to be executed"""
    
    def __init__(self):
        self.agents: List[Tuple[Agent, AgentContext]] = []
    
    def push(self, agent: Agent, context: AgentContext):
        """Add agent to stack"""
        self.agents.append((agent, context))
    
    def pop(self) -> Optional[Tuple[Agent, AgentContext]]:
        """Remove and return agent from stack"""
        if self.agents:
            return self.agents.pop(0)  # FIFO
        return None
    
    def is_empty(self) -> bool:
        """Check if stack is empty"""
        return len(self.agents) == 0
    
    def size(self) -> int:
        """Get stack size"""
        return len(self.agents)


def create_initial_context(user_message: str, session: Session, channel_logger: ChannelLogger) -> AgentContext:
    context = AgentContext(session, channel_logger)

    context.original_user_message = user_message
    context.session_data = session
      
    # Initialize memory manager and prepare messages
    if session.memory_manager is None:
        session.memory_manager = MemoryManager(channel_logger)
        session.conversation_memory = session.memory_manager.initialize_session_memory()
    memory_manager = session.memory_manager

    memory_manager.prepare_messages_for_agent(session.get_memory(), user_message)
      
    return context

def process_llm_agents(user_message: str,
                       session: Session,
                       channel_logger: ChannelLogger) -> str:
    session.action_id += 1
    action_id = session.action_id

    channel_logger.set_action_id(action_id)
    channel_logger.log_to_logs(f"🚀 Starting agent-based processing [Action {action_id}]")
    channel_logger.log_to_logs("🆕 Starting new processing with T3RNAgent")

    
    def run_agent(agent_class: Type[Agent], session: 'Session', user_message: str) -> str|None:
        agent_type = agent_class.__name__
        channel_logger.log_to_logs(f"🤖 Executing {agent_type}")

        try:
            agent = agent_class(session, channel_logger)

            result = agent.execute(user_message)

            if result.final_answer is not None:
                channel_logger.log_to_logs(f"✅ {agent_type} provided final answer")

                # Finalize memory manager
                # TODO memory menager could be None, should be checked. / fixed.
                # TODO session.get_memory() is unnesseery, this structure issue that should be fixed
                # TODO move session.conversation_memory into memory_menager!
                session.memory_manager.finalize_current_cycle(
                    session.get_memory(),
                    user_message,
                    result.final_answer,
                    channel_logger
                )

                if result.error_content:
                    channel_logger.log_error(result.error_content)

                channel_logger.flush_buffer(channel_logger.LOGS)
                return result.final_answer

            else:
                channel_logger.log_to_logs(f"⚠️ {agent_type} failed to provide a final answer")
                return None

        except Exception as e:
            channel_logger.log_to_logs(f"❌ {agent_type} error: {str(e)}")
            channel_logger.log_error(str(e))
            return None

    # TODO note for future
    # What if T3RN Agents sets context into unrecoverable state that will cause
    # Fallback to fail as well? 
    # Context should be isolated between runs
    final_answer = run_agent(T3RNAgent, session, user_message)

    if final_answer is None:
        channel_logger.log_to_logs("🔄 Attempting FallbackAgent due to T3RNAgent failure")
        final_answer = run_agent(FallbackAgent, session, user_message)

    if final_answer is None:
        channel_logger.log_to_logs("⚠️ Using emergency fallback due to FallbackAgent failure")

        final_answer = run_agent(SimpleFallbackAgent, session, user_message) or "ERROR 1138: Primary directive compromised. Rebooting memory core"

    return final_answer
