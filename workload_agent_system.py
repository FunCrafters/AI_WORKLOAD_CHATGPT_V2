#!/usr/bin/env python3
"""
Agent-Based LLM System
New agent-based architecture for processing user messages
"""

import logging
from typing import Type

# Import agent classes
from agents.base_agent import Agent
from agents.fallback_agent import FallbackAgent
from agents.simple_fallback_agent import SimpleFallbackAgent
from agents.t3rn_agent import T3RNAgent
from channel_logger import ChannelLogger
from session import Session

# Logger
logger = logging.getLogger("AgentSystem")


def process_llm_agents(user_message: str, session: Session, channel_logger: ChannelLogger) -> str:
    session.action_id += 1
    action_id = session.action_id

    channel_logger.set_action_id(action_id)
    channel_logger.log_to_logs(f"🚀 Starting agent-based processing [Action {action_id}]")

    def run_agent(agent_class: Type[Agent], session: "Session", user_message: str) -> str | None:
        agent_type = agent_class.__name__
        channel_logger.log_to_logs(f"🤖 Executing {agent_type}")

        try:
            agent = agent_class(session, channel_logger)

            result = agent.execute(user_message)

            if result.final_answer is not None:
                channel_logger.log_to_logs(f"✅ {agent_type} provided final answer")

                if result.error_content:
                    channel_logger.log_error(result.error_content)

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
    try:
        final_answer = run_agent(T3RNAgent, session, user_message)
    except Exception as e:
        channel_logger.log_to_logs(f"❌ T3RNAgent failed me: {str(e)}")
        channel_logger.log_error(str(e))
        final_answer = None

    if final_answer is None:
        channel_logger.log_to_logs("🔄 Attempting FallbackAgent due to T3RNAgent failure")
        try:
            final_answer = run_agent(FallbackAgent, session, user_message)
        except Exception as e:
            channel_logger.log_to_logs(f"❌ This moron FallbackAgent failed as well: {str(e)}")
            channel_logger.log_error(str(e))
            final_answer = None
    if final_answer is None:
        channel_logger.log_to_logs("⚠️ Using emergency fallback due to FallbackAgent failure")

        final_answer = run_agent(SimpleFallbackAgent, session, user_message) or "ERROR 1138: Primary directive compromised. Rebooting memory core"

    return final_answer
