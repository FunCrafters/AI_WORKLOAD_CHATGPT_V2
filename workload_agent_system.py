#!/usr/bin/env python3
"""
Agent-Based LLM System
New agent-based architecture for processing user messages
"""

import logging
from typing import Type

# Import agent classes
from agents.base_agent import Agent
from agents.simple_fallback_agent import SimpleFallbackAgent
from agents.t3rn_agent import T3RNAgent
from agents.fallback_agent import FallbackAgent
from channel_logger import ChannelLogger
from session import Session

# Logger
logger = logging.getLogger("Agent System")

def process_llm_agents(user_message: str,
                       session: Session,
                       channel_logger: ChannelLogger) -> str:
    session.action_id += 1
    action_id = session.action_id

    channel_logger.set_action_id(action_id)
    channel_logger.log_to_logs(f"🚀 Starting agent-based processing [Action {action_id}]")
    
    if session.memory_manager is None:
        raise Exception("Memory must be initalized")
 
    def run_agent(agent_class: Type[Agent], session: 'Session', user_message: str) -> str|None:
        agent_type = agent_class.__name__
        channel_logger.log_to_logs(f"🤖 Executing {agent_type}")
        if session.memory_manager is None:
            raise Exception("Memory must be initalized")

        try:
            agent = agent_class(session, channel_logger)

            result = agent.execute(user_message)

            if result.final_answer is not None:
                channel_logger.log_to_logs(f"✅ {agent_type} provided final answer")

                # Finalize memory manager
                # TODO memory menager could be None, should be checked. / fixed.
                session.memory_manager.finalize_current_cycle(
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
