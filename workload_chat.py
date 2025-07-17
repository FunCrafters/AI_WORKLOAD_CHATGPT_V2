#!/usr/bin/env python3
"""
Workload Chat Functions
Chat processing functionality for the workload
"""

import logging
import time

# Import agent system
from agents.memory_manager import MemoryManager

# Import channel logger
from channel_logger import ChannelLogger
from session import Session
from workload_agent_system import process_llm_agents
from workload_tools import ContextAdapter, create_response, send_response

# Logger
logger = logging.getLogger("Workload Chat")
logger = ContextAdapter(logger)
#######################
# Main Processing Function
#######################


# TODO Send response should not be passed as a parameter to process_main_channel!
def process_main_channel(client, session: "Session"):
    """Process text on the main channel (0) with agent-based function calling"""
    session_id = session.session_id
    message_id = session.message_id
    channel = session.channel
    text = session.user_message.strip() if session.user_message else ""

    if not text:
        response = create_response(channel, "", session_id, message_id)
        send_response(client, response, session_id, channel or 0, message_id)
        return

    session.session_id = session_id

    # Create channel logger for multi-channel logging
    channel_logger = ChannelLogger(client, session_id, session.message_id)

    if session.memory_manager is None:
        session.memory_manager = MemoryManager(channel_logger)

    # Initial logging
    channel_logger.log_to_logs(f'🚀 Processing with Agent-Based System: "{text}"')
    channel_logger.log_to_logs(f"💬 Session ID: {session_id}")

    logger.info("   AGENT-BASED PROCESSING", extra=dict(session_id=session_id))

    try:
        # Process with agent-based function calling
        start_time = time.time()
        final_answer = process_llm_agents(text, session, channel_logger)
        process_time = time.time() - start_time

        channel_logger.log_to_logs(
            f"✅ Agent processing completed in {process_time:.2f} seconds"
        )
        channel_logger.log_to_logs(f"📝 Answer length: {len(final_answer)} characters")
        session.memory_manager.log_memory()

        chat_response = create_response(0, final_answer, session_id, message_id)
        send_response(client, chat_response, session_id, channel or 0, message_id)

    except Exception as e:
        logger.info(
            "!! AGENT PROCESSING ERROR", extra=dict(session_id=session_id, error=str(e))
        )

        import traceback

        error_traceback = traceback.format_exc()
        logger.error(error_traceback)

        action_id = session.action_id
        channel_logger.set_action_id(action_id)
        channel_logger.log_exception(e, error_traceback)

        channel_logger.log_to_chat(f"Error processing your question: {str(e)}")
