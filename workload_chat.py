#!/usr/bin/env python3
"""
Workload Chat Functions
Chat processing functionality for the workload
"""

import time
import logging

# Import agent system
from session import Session
from workload_agent_system import (
    process_llm_agents
)

# Import channel logger
from channel_logger import ChannelLogger
from workload_tools import ContextAdapter, create_response, send_response

# Logger
logger = logging.getLogger("Workload Chat")
logger = ContextAdapter(logger)

#######################
# Main Processing Function
#######################

# TODO Send response should not be passed as a parameter to process_main_channel!
def process_main_channel(client, session: 'Session'):
    """Process text on the main channel (0) with agent-based function calling"""
    session_id = session.session_id
    message_id = session.message_id
    channel = session.channel
    text = session.text.strip() if session.text else ""
    
    if not text:
        response = create_response(channel, "", session_id, message_id)
        send_response(client, response, session_id, channel, message_id)
        return
    
    session.client = client
    session.session_id = session_id
    
    # Create channel logger for multi-channel logging
    channel_logger = ChannelLogger(client, session_id, session.message_id)
    
    # Import available functions count from LLM module
    from tools_functions import available_llm_functions
    
    # Initial logging
    channel_logger.log_to_logs(f"🚀 Processing with Agent-Based System: \"{text}\"")
    channel_logger.log_to_logs(f"💬 Session ID: {session_id}")
    channel_logger.log_to_logs(f"🔧 Available tools: {len(available_llm_functions)} tools")
        
    logger.info(f"   AGENT-BASED PROCESSING", extra=dict(session_id=session_id))
    
    try:
        # Process with agent-based function calling
        start_time = time.time()        
        final_answer = process_llm_agents(text, session, channel_logger)
        process_time = time.time() - start_time

        channel_logger.log_to_logs(f"✅ Agent processing completed in {process_time:.2f} seconds")
        channel_logger.log_to_logs(f"📝 Answer length: {len(final_answer)} characters")
        
        chat_response = create_response(0, final_answer, session_id, message_id)
        send_response(client, chat_response, session_id, channel, message_id)
      
    except Exception as e:
        logger.info("!! AGENT PROCESSING ERROR", extra=dict(session_id=session_id, error=str(e)))
        
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        action_id = session.action_id 
        channel_logger.set_action_id(action_id)
        channel_logger.log_exception(e, error_traceback)
        
        channel_logger.log_to_chat(f"Error processing your question: {str(e)}")
    
